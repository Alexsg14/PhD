import { compile } from 'mathjs';

export const N_BINS = 100;
export const MIN_X = -2.5;
export const MAX_X = 2.5;
export const DX = (MAX_X - MIN_X) / N_BINS;

// Encapsulate the global state of the simulation
export const state = {
    GAMMA: 5.0,
    BETA: 1.0,
    ENERGY_BARR: 15.0,
    EPSILON: 0,
    NORM_FACTOR: 1.0,
    STEPS_PER_FRAME: 50,
    
    x_space: [],
    FES_true: [],
    Prob_target: [],
    Prob_unbiased: [],
    
    weighted_counts: new Array(N_BINS).fill(0),
    sum_weights: 0,
    sum_weights2: 0,
    sigma_0: 0.2,
    
    Prob_est: new Array(N_BINS).fill(0),
    Bias: new Array(N_BINS).fill(0),
    Histogram: new Array(N_BINS).fill(0),
    
    current_x: -1.0,
    isRunning: false,
    lastError: ""
};

export function initSystem(gamma, beta, barrier, speed, equationStr = "2.0 * (x^4 - 4*x^2 + 0.5*x) + 10.0") {
    state.GAMMA = gamma;
    state.BETA = beta;
    state.ENERGY_BARR = barrier;
    state.STEPS_PER_FRAME = speed;

    state.x_space = [];
    state.FES_true = [];
    state.Prob_target = [];
    state.Prob_unbiased = [];
    
    state.Prob_est.fill(0);
    state.Bias.fill(0);
    state.Histogram.fill(0);
    state.weighted_counts.fill(0);
    state.current_x = -1.0;

    let factor = 1.0 - 1.0 / state.GAMMA;
    state.EPSILON = Math.exp((-state.BETA * state.ENERGY_BARR) / factor);
    state.NORM_FACTOR = Math.pow(state.EPSILON, factor);

    state.sum_weights = state.NORM_FACTOR;
    state.sum_weights2 = state.NORM_FACTOR * state.NORM_FACTOR;

    let Z_target = 0;
    let Z_unbiased = 0;
    
    let evaluateFn;
    try {
        const node = compile(equationStr);
        evaluateFn = (x) => node.evaluate({ x });
        evaluateFn(0); // Test execution
        state.lastError = "";
    } catch (err) {
        state.lastError = "Invalid equation: " + err.message;
        const node = compile("2.0 * (x^4 - 4*x^2 + 0.5*x) + 10.0");
        evaluateFn = (x) => node.evaluate({ x });
    }

    for (let i = 0; i < N_BINS; i++) {
        let x = MIN_X + i * DX;
        state.x_space.push(x.toFixed(2));

        let e = evaluateFn(x);
        state.FES_true.push(e);

        let p_tg = Math.exp(-state.BETA * e / state.GAMMA);
        state.Prob_target.push(p_tg);
        Z_target += p_tg * DX;

        let p_un = Math.exp(-state.BETA * e);
        state.Prob_unbiased.push(p_un);
        Z_unbiased += p_un * DX;
    }

    for (let i = 0; i < N_BINS; i++) {
        state.Prob_target[i] /= Z_target;
        state.Prob_unbiased[i] /= Z_unbiased;
    }
}

export function updateOPES() {
    if (state.sum_weights === 0) return;

    // Silverman's rule for KDE shrinkage (n_eff)
    let n_eff = Math.pow(1.0 + state.sum_weights, 2) / (1.0 + state.sum_weights2);

    // sigma_i = sigma_0 * ( (n_eff * 3/4)^(-1/5) ) for 1 Dimension
    let sigma_i = state.sigma_0 * Math.pow((n_eff * 3.0 / 4.0), -0.2);
    sigma_i = Math.max(sigma_i, DX * 0.8);

    let Z_n = 0;
    let prob_unnorm = new Array(N_BINS).fill(0);
    const inv_sigma2 = 1.0 / (sigma_i * sigma_i);

    for (let i = 0; i < N_BINS; i++) {
        let x_i = MIN_X + i * DX;
        let p_x = 0;
        for (let j = 0; j < N_BINS; j++) {
            if (state.weighted_counts[j] > 0) {
                let x_j = MIN_X + j * DX;
                let dist = x_i - x_j;
                p_x += state.weighted_counts[j] * Math.exp(-0.5 * (dist * dist) * inv_sigma2);
            }
        }
        prob_unnorm[i] = p_x / state.sum_weights;
        Z_n += prob_unnorm[i] * DX;
    }

    let factor = 1.0 - 1.0 / state.GAMMA;

    for (let i = 0; i < N_BINS; i++) {
        // p_norm is \tilde{P}_n(s) / Z_n from eq 8
        let p_norm = prob_unnorm[i] / (Z_n > 0 ? Z_n : 1);
        state.Prob_est[i] = p_norm;

        let log_term = Math.log(p_norm + state.EPSILON);
        state.Bias[i] = factor * (1.0 / state.BETA) * log_term;
    }
}

export function simulationStep() {
    for (let step = 0; step < state.STEPS_PER_FRAME; step++) {
        // Monte Carlo random proposal
        let dx = (Math.random() - 0.5) * 0.8;
        let x_new = state.current_x + dx;

        if (x_new < MIN_X) x_new = MIN_X + 0.01;
        if (x_new >= MAX_X) x_new = MAX_X - 0.01;

        let idx_curr = Math.max(0, Math.min(N_BINS - 1, Math.floor((state.current_x - MIN_X) / DX)));
        let E_curr = state.FES_true[idx_curr] + state.Bias[idx_curr];

        let idx_new = Math.max(0, Math.min(N_BINS - 1, Math.floor((x_new - MIN_X) / DX)));
        let E_new = state.FES_true[idx_new] + state.Bias[idx_new];

        // Metropolis acceptance criterion
        if (Math.exp(-state.BETA * (E_new - E_curr)) > Math.random()) {
            state.current_x = x_new;
            idx_curr = idx_new;
        }

        state.Histogram[idx_curr]++;

        if (step % 5 === 0) {
            let w = Math.exp(state.BETA * state.Bias[idx_curr]);
            state.weighted_counts[idx_curr] += w;

            state.sum_weights += w;
            state.sum_weights2 += (w * w);
        }
    }
    updateOPES();
}
