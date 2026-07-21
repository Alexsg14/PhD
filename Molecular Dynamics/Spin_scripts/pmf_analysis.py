import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import griddata
import matplotlib.cm as cm
from os.path import exists
from matplotlib.colors import LogNorm
import matplotlib as mpl
from matplotlib.colors import Normalize
from scipy.spatial import ConvexHull #volumen calcular
from matplotlib.colors import DivergingNorm
#from vedo import *
#import plotly.express as px
#import plotly.graph_objects as go
#ctes:
T=300;R=8.314472/1000.
################################################################################
#                   FUNCIÓN PARA EL CÁLCULO DEL ÁREA                           #
################################################################################
from sklearn.metrics import roc_curve,auc
def area(x,y,xmin,xmax,globalmin,T=298,R=8.314472/1000.):#listas de puntos en las coordenadas x e y, asi como el rango en x max y min
    x_corregida=[]#listas vacias para quedarnos con los elementos en x e y de interés
    y_corregida=[]
    y_corregida_exp=[]
    maxima=np.exp(max(-y)/(T*R))
    print('XMAX: ',xmax,'XMIN: ',xmin)
    if xmin<xmax:
        xmin2=xmin
        xmax2=xmax
    else:
        xmin2=xmax
        xmax2=xmin
    for i in range(len(x)):
        if (x[i])>(xmin2) and (x[i])<(xmax2):
            x_corregida.append(x[i])
            y_corregida.append(y[i])
    #return x_corregida,y_corregida#max(y_corregida)-y_corregida
    for elemento in y_corregida:
        y_corregida_exp.append(np.exp(-(elemento-globalmin)/(T*R)))
    norma=np.sum(y_corregida_exp)#menos
    areas=auc(x_corregida,y_corregida_exp)#maxima-y_corregida_exp
    return x_corregida,y_corregida_exp,areas#maxima-y_corregida_exp,areas
################################################################################
######################## INPUTS ################################################
################################################################################
#Aquí se seleccionan los valores máximos y mínimos de las dos CVS que se esten empleando CV1, CV2
cv1min=-8
cv1max=-0.5
cv2min=-3.14
cv2max=3.14
#Aquí los valores máximos y mínimos del perfil energético
pmfmax_=110;pmfmax=pmfmax_;factor=pmfmax/abs(pmfmax)
pmfmin_=0
# Read 2D fes file
cambio_de_ejes=1 #1 o -1
abrir=np.loadtxt('POSICION_PLANO.dat')
binding_free=abrir*cambio_de_ejes
print('BINDING: ',binding_free)




df=pd.DataFrame(pd.read_csv('fesd1d2.dat',delim_whitespace=True, header=None, skiprows=9))

#Variables x, y e z del archivo fesd1d2.dat
x=df[df.columns[0]].to_numpy()*cambio_de_ejes#Este -1, depende de la definición inicial, igual en tu caso se puede borrar
y=df[df.columns[1]].to_numpy()
z=df[df.columns[2]].to_numpy()
globalmin=0#;globalmin_p=108
z=z-globalmin
#Creamos un gradiente para a representación gráfica
xi = np.linspace(np.min(x), np.max(x), 1000)
yi = np.linspace(np.min(y), np.max(y), 1000)
zi = griddata((x, y), z, (xi[None,:], yi[:,None]), method='linear')
#contamos el número de 1D fes files
nfesfiles=0
for i in range(1,1000): # Detect number of 1D fes files
    if exists("fesd1_"+str(i)+".dat"): nfesfiles=nfesfiles+1
    else: break
n1Dplots=int(nfesfiles*10/100)#Representamos el 30% de los últimos valores
xd1=[];yd1=[];xd2=[];yd2=[];yd1_trans=[];yd2_trans=[]
for i in range(nfesfiles,nfesfiles-n1Dplots,-1): # Read last 10 1D fes files
    df1Dd1=pd.DataFrame(pd.read_csv("fesd1_"+str(i)+".dat",delim_whitespace=True, header=None, skiprows=5))
    df1Dd2=pd.DataFrame(pd.read_csv("fesd2_"+str(i)+".dat",delim_whitespace=True, header=None, skiprows=5))#-df[df.columns[2]].to_numpy()/(R*T)
    xd1.append(df1Dd1[df1Dd1.columns[0]].to_numpy()); yd1.append(df1Dd1[df1Dd1.columns[1]].to_numpy()-globalmin);yd1_trans.append(np.exp(-(df1Dd1[df1Dd1.columns[1]].to_numpy()-globalmin)/(R*T))/np.sum(np.exp(-(df1Dd1[df1Dd1.columns[1]].to_numpy()-globalmin)/(R*T))))#OJO -
    xd2.append(df1Dd2[df1Dd2.columns[0]].to_numpy()); yd2.append(df1Dd2[df1Dd2.columns[1]].to_numpy()-globalmin);yd2_trans.append(np.exp(-(df1Dd2[df1Dd2.columns[1]].to_numpy()-globalmin)/(R*T))/np.sum(np.exp(-(df1Dd2[df1Dd2.columns[1]].to_numpy()-globalmin)/(R*T))))#OJO -

a=np.loadtxt('CV1_BA.dat')
energia=a[:,1]
pos=a[:,0]*cambio_de_ejes*-1
inc=a[:,2]
y_incerteza=[]
for u in range(len(pos)):
    if abs(pos[u])<6 and abs(pos[u])>4:
        y_incerteza.append(yd1[0][u])
plato=np.mean(y_incerteza);plato_inc=np.std(y_incerteza)
pmfmax=pmfmin_
pmfmin=-1*pmfmax_


#Representación gráfica
fig, axs = plt.subplots(nrows=2, ncols=2, gridspec_kw={'width_ratios': [3, 1], 'height_ratios': [1, 3]},figsize = (20, 10), dpi=81)
axs = axs.flatten()
for i in range(1,n1Dplots):
    axs[0].plot(xd1[i]*cambio_de_ejes, yd1[i]-plato)#O -1 depende da tua definición de coordenada x.
    axs[3].plot(yd2[i]-plato, xd2[i])
axs[1].axis('off')
axs[3].yaxis.tick_right()
levels=list(range(int(pmfmin), int(pmfmax),5))#Niveles a representar
#print(levels)
#levels=np.sort(levels)
cpf = axs[2].contourf(xi, yi, zi-plato,1000,vmin=min(levels),vmax=max(levels),extend='both',cmap=cm.jet.reversed(),ticks=levels,levels=levels)
cpf.changed()#contourf
#Representamos la barra del gradiente de colores
levels2=list(range(int(pmfmin), int(pmfmax), 10))#Niveles a representar

cbar =fig.colorbar(cpf,ax=axs[3],ticks=levels2,boundaries=levels)
cbar.ax.tick_params(labelsize=22)
#cbar.set_clim(pmfmin,pmfmax)
cpf.changed()
#cbar.ax.set_ylim(levels[0], levels[-1])
cp = axs[2].contour(xi, yi, zi-plato, levels, colors='black', linestyles='dashed')
axs[2].clabel(cp, fmt='%d',fontsize=1, colors='black') #LABELS DEL CONTORNO
axs[2].clabel(cp, fmt='%d',fontsize=12, colors='black') #Tamaño de los labels del contorno
axs[0].get_xaxis().set_visible(False)
axs[0].set_ylabel(r'$\mathbf{\Delta G\,\, (kJ/mol)}$', fontsize=24)
axs[2].axis([cv1min,cv1max,cv2min,cv2max])
axs[2].set_xlabel(r'$\mathbf{ Distance\,\, (nm)}$', fontsize=24)
axs[2].set_ylabel(r'$\mathbf{ Cos (\phi)}$', fontsize=24)
axs[2].set_ylim(cv2min,cv2max)
axs[0].tick_params(axis='both', which='major', labelsize=20)
axs[1].tick_params(axis='both', which='major', labelsize=20)
axs[2].tick_params(axis='both', which='major', labelsize=20)
axs[3].tick_params(axis='both', which='major', labelsize=20)

#Limites da gráfica
axs[2].set_xlim(cv1min,cv1max)
axs[0].set_xlim(cv1min,cv1max)
axs[3].axis([levels[0],levels[-1],cv2min,cv2max])
axs[3].get_yaxis().set_visible(False)
axs[3].set_xlabel(r'$\mathbf{\Delta G\,\, (kJ/mol)}$', fontsize=24)
axs[3].set_ylim(cv2min,cv2max)
##################################
#-----INCERTIDUMBRE----------#####
##################################
a=np.loadtxt('CV1_BA.dat')
energia=a[:,1]
pos=a[:,0]*cambio_de_ejes*-1
inc=a[:,2]
axs[0].plot(-pos,yd1[0]-plato,color='green')



print('PLATO: ',plato,'+-',plato_inc)
#Observamos en que valor empieza a decaer
#print(yd1[0]-plato)
axs[0].fill_between(-pos, np.array(yd1[0]-plato)-np.array(inc),np.array(yd1[0]-plato)+np.array(inc),alpha=0.3,color='green')
a=np.loadtxt('CV2_BA.dat')
energia=a[:,1]
pos=a[:,0]
inc=a[:,2]
angulo_promedio_inc=np.mean(inc)
axs[3].plot(yd2[0]-plato,(pos),color='green')
axs[3].fill_betweenx((np.array(pos)), np.array(yd2[0]-plato)-np.array(inc),np.array(yd2[0]-plato)+np.array(inc),alpha=0.2,color='green')
axs[2].set_xlim(cv1min,cv1max)
axs[0].set_xlim(cv1min,cv1max)
from matplotlib.ticker import MaxNLocator
axs[0].yaxis.set_major_locator(MaxNLocator(4))
axs[0].set_ylim(pmfmin-10,pmfmax+10)
axs[3].set_xlim(pmfmin-10,pmfmax+10)

#Generamos linea posición fosforos
y_sup=np.linspace(-500,500,100)
limite_inf=np.linspace(-1.97,-1.97,100)
axs[0].plot(limite_inf,y_sup,linestyle='dotted',color='red',label='HGs')
interaccion_y=np.linspace(-500,500,100)
interaccion_x=np.linspace(binding_free,binding_free,100)
from matplotlib.ticker import FormatStrFormatter
#axs[0].plot(interaccion_x,interaccion_y,linestyle='--',color='k',label='F/B')
axs[2].yaxis.set_major_formatter(FormatStrFormatter('%.1f'))


#axs[0].legend(fontsize=22)
#axs[0].text(-2.2,-250,'HGs',color='red',fontsize=22)
#axs[0].text(binding_free-0.2,-250,'F/B',color='black',fontsize=22)

axs[3].xaxis.set_major_locator(MaxNLocator(3))
axs[3].minorticks_on()
axs[0].minorticks_on()
axs[2].minorticks_on()

leer_tiempo=np.loadtxt('HILLS') #Para dar nombre al archivo PNG que saca
ultimo_tiempo=leer_tiempo[:,0]

axs[2].text(cv1min+1,cv2max-1,str(int(ultimo_tiempo[-1]))+' ns', fontsize=22, color='white')

plt.tight_layout(pad = 1, w_pad = 2, h_pad = 2)
#plt.savefig("PMF_"+str(int(ultimo_tiempo[-1]))+"_coseno.png")
plt.savefig("PMF_"+str(int(ultimo_tiempo[-1]))+"_AAAAAAA.png")
#plt.savefig("fes.png")
plt.show()
plt.close()
