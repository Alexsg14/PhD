import numpy as np
import matplotlib.pyplot as plt
############################################################################################################
#                                 FUNCIÓN PARA O CÁLCULO DO BA                                             #
############################################################################################################
def blockAverage(datos,tamaño_bloque_maximo=False,grafica=True):
    "Método para calcular incertidumes con datos correlacionados temporalmente, block-avarage. Sería ideal engadir o método de bootstraping para comparar"
    Nobs = len(datos) # número total de datos, dar un array ou lista
    tamaño_bloque_minimo=1 # mínimo tamaño de bloque, corresponde a non facer block_avarage
    if tamaño_bloque_maximo==False:
        tamaño_bloque_maximo=int(Nobs/4)#Criterio por se non se selecciona un dato óptimo de bloque
    Numero_de_bloques = tamaño_bloque_maximo-tamaño_bloque_minimo # total number of block sizes
    Media_bloque = np.zeros(Numero_de_bloques) 
    co = np.zeros(Numero_de_bloques) # definese no seguinte papper, pero é a varianza
    #print('A información do método atópase en:  https://doi.org/10.1063/1.457480')
    bloqueCtr=0
    incertidume=np.zeros(Numero_de_bloques)
    barra_erros=np.zeros(Numero_de_bloques)
    for datos_bloque in range(tamaño_bloque_minimo,tamaño_bloque_maximo):
        Nbloque=int(Nobs/datos_bloque) # En que bloque estou según o numero de observacions
        almacenamento_temporal=np.zeros(Nbloque) # isto é para almacenar a media según en que bloque esté, é temporal
        # Loop to chop datastream into blocks
        # and take average
        for i in range(1,Nbloque+1):
            #Esta é a parte máis complicada do código pois (fago de 1 a N+1, para empregar logo as definicións matemáticas)
            #E como vou calculando as medias según o bloque no que me atope, e dicir o número de datos por bloque
            comeza = (i-1)*datos_bloque
            remata = comeza+datos_bloque
            almacenamento_temporal[i-1] = np.mean(datos[comeza:remata])
        Media_bloque[ bloqueCtr] = np.mean(almacenamento_temporal)
        co[bloqueCtr]  = np.var(almacenamento_temporal)
        incertidume[ bloqueCtr]=np.sqrt(np.var(almacenamento_temporal)/((Nbloque-1)))
        barra_erros[ bloqueCtr]=np.sqrt(np.var(almacenamento_temporal)/(Nbloque-1))*1/(np.sqrt(2*(Nbloque-1)))
        bloqueCtr=bloqueCtr+1
    tamaño_bloque= np.arange(tamaño_bloque_minimo,tamaño_bloque_maximo)
    if grafica:
        plt.errorbar(tamaño_bloque, incertidume,barra_erros, marker='o',ls='None',markersize=8, capsize=6)
        plt.xlabel('Tamaño do bloque (Número de datos por bloque, que deben ter todos o mesmo tamaño)')
        plt.ylabel('Desviación estándar')
        plt.show()
        plt.errorbar(tamaño_bloque, Media_bloque, incertidume,marker='o',ls='None',markersize=8, capsize=6,color='Orange')
        plt.ylabel('Media')
        plt.xlabel('Tamaño do bloque')
        plt.show()
        plt.tight_layout()
        plt.show()
        #print(f"Valor medio = {Media_bloque[-1]:.3f} +/- {incertidume[-1]:.3f}")
    return tamaño_bloque, Media_bloque, incertidume
############################################################################################################
############################################################################################################
############################################################################################################



#Cargamos módulos
import pandas as pd
from os.path import exists

#Contador nulo  de archivos fes
nfesfiles=0
globalmin=0

#contamos o numero de fes
for i in range(1,100000): # Detect number of 1D fes files
    if exists("fesd1_"+str(i)+".dat"): nfesfiles=nfesfiles+1
    else: break
n1Dplots=int(nfesfiles*30/100)#representar el 30%
xd1=[];yd1=[];xd2=[];yd2=[]#array para almacenar la información de los archivos fes
for i in range(nfesfiles,nfesfiles-n1Dplots,-1): # Read last  1D fes files
    df1Dd1=pd.DataFrame(pd.read_csv("fesd1_"+str(i)+".dat",delim_whitespace=True, header=None, skiprows=5))
    df1Dd2=pd.DataFrame(pd.read_csv("fesd2_"+str(i)+".dat",delim_whitespace=True, header=None, skiprows=5))
    xd1.append(df1Dd1[df1Dd1.columns[0]].to_numpy()); yd1.append(df1Dd1[df1Dd1.columns[1]].to_numpy()-globalmin)
    xd2.append(df1Dd2[df1Dd2.columns[0]].to_numpy()); yd2.append(df1Dd2[df1Dd2.columns[1]].to_numpy()-globalmin)
print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
print('-----------------------------------------------')
print('Lectura de los archivos completada')
print('-----------------------------------------------')
print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
print('')
############################################################################################################
#                                 ESTE BLOQUE TENGO QUE ORDENARLO                                          #
############################################################################################################
CV1 = np.array(xd1)
energia_CV1=np.array(yd1)
with open('CV1_BA.dat','w') as files:
    for i in range (len(CV1[0])):
        tamaño_bloque, Media_bloque, incertidume=blockAverage(energia_CV1[:,i],grafica=False)
        files.write(str(CV1[0,i])+'   '+ str(Media_bloque[-1])+'   '+str(incertidume[-1])+"\n")

CV2=np.array(xd2)
energia_CV2=np.array(yd2)
with open('CV2_BA.dat','w') as files:
    for i in range (len(CV2[0])):
        tamaño_bloque, Media_bloque, incertidume=blockAverage(energia_CV2[:,i],grafica=False)
        files.write(str(CV2[0,i])+'   '+ str(Media_bloque[-1])+'   '+str(incertidume[-1])+"\n")
################################################################################################################################################
################################################################################################################################################
def media_movil(x,n):
    resultado=[]
    for i in range(n):
        if i==0:
            pass
        else:
            resultado.append(float((np.sum(x[0:i])/len(x[0:i]))))
    cumsum=np.cumsum(np.insert(x, 0, 0))
    res=(cumsum [n:]-cumsum[:-n])/float(n)
    for elemento in res:
        resultado.append(elemento)
    return resultado
################################################################################################################################################
################################################################################################################################################
orden_cv1=int(len(energia_CV1)/1.4)
orden_cv2=int(len(energia_CV2)/1.4)
print('')
print('-----------------------------------------------------------------------')
print('Cálculo de la diferencia entre el mínimo y la parte plana de la función')
print('-----------------------------------------------------------------------')
archivo_cv1=np.loadtxt('CV1_BA.dat')
ejes=1
energia_cv1=archivo_cv1[:,1]
energia_cv1=energia_cv1[::ejes]#energia_cv1.reverse()

energia_cv1_n=media_movil(energia_cv1,orden_cv1)
posicion_cv1=archivo_cv1[:,0]*ejes
incertidumbre_cv1=archivo_cv1[:,2]
plt.plot(posicion_cv1,energia_cv1,color='blue')
plt.plot(posicion_cv1,energia_cv1_n,color='orange')

plt.fill_between(posicion_cv1, np.array(energia_cv1)-np.array(incertidumbre_cv1),np.array(energia_cv1)+np.array(incertidumbre_cv1),alpha=0.2,color='blue')
plt.fill_between(posicion_cv1, np.array(energia_cv1_n)-np.array(incertidumbre_cv1),np.array(energia_cv1_n)+np.array(incertidumbre_cv1),alpha=0.2,color='orange')

def buscar_parte_plana(posicion,CV,energia,incertidumbre,limite_busqueda=40,CV1=False,CV2=False):
    print(f'Calculando para {CV:s}...')
    for i in range(len(posicion)):
        try:
            if i<limite_busqueda:
                pass
            elif i==len(posicion)-1:
                print(f'No se ha encontrado parte plana en {CV:s}');promediam='NULL'
            else:
                margen_1=int(np.mean(energia[i-limite_busqueda:i]));margen_2=int(np.mean(energia[i:i+limite_busqueda]))
                if  int(energia[i])==margen_1 and int(energia[i])==margen_2 and int(energia[i])==int(energia[i+limite_busqueda]) and energia[i]<margen_1+incertidumbre[i] and energia[i]>margen_1-incertidumbre[i] and energia[i]<margen_2+incertidumbre[i] and energia[i]>margen_2-incertidumbre[i]:
                    if CV1==True:
                        print('A: ',archivo_cv1[i,1]);promediam=archivo_cv1[i,1]
                        print(f"Valor medio {CV:s}= {archivo_cv1[i,1]:.3f} +/- {archivo_cv1[i,2]:.3f}")
                        break
                    elif CV2==True:
                        print(f"Valor medio {CV:s}= {archivo_cv1[i,1]:.3f} +/- {archivo_cv1[i,2]:.3f}")
                        promediam='CV2'
                        break
        except IndexError or ValueError:
            print(f'No se ha encontrado parte plana en {CV:s}');promediam='NULL'
    return promediam
plana_cv1=buscar_parte_plana(posicion_cv1,'CV1',energia_cv1,incertidumbre_cv1,40,True,False)
#Posicion rompe parte plana:
#Metodo lineas se separan
print('Busqueda de la posición de separación):')
metodos=[]
promedio=np.mean(energia_cv1[0:102])#de la parte plana
promedio=plana_cv1
for elemento in range(len(energia_cv1_n)):
    if energia_cv1_n[elemento]-incertidumbre_cv1[elemento]<promedio+incertidumbre_cv1[elemento] and energia_cv1_n[elemento]+incertidumbre_cv1[elemento]>promedio-incertidumbre_cv1[elemento] or abs(posicion_cv1[elemento])>6:
        continue
    else:
        print('Posicion METODO 1: ',posicion_cv1[elemento])
        metodos.append(posicion_cv1[elemento])
        break


print('PROMEDIO: ',promedio)
for elemento in range(len(energia_cv1)):
    if energia_cv1[elemento]<promedio+incertidumbre_cv1[elemento] and energia_cv1[elemento]>promedio-incertidumbre_cv1[elemento] or abs(posicion_cv1[elemento])>6:
        continue
    else:
        print('Posicion METODO 2: ',posicion_cv1[elemento])

        metodos.append(posicion_cv1[elemento])
        break
with open('POSICION_PLANO.dat','w') as files:
        files.write(str(np.mean(metodos)))
#for elemento in range(energia_cv1):
    


plt.show()
plt.close()
archivo_cv2=np.loadtxt('CV2_BA.dat')
energia_cv2=archivo_cv2[:,1]
energia_cv2=media_movil(energia_cv2,orden_cv2)
posicion_cv2=archivo_cv2[:,0]
incertidumbre_cv2=archivo_cv2[:,2]
plt.plot(posicion_cv2,energia_cv2,color='blue')
plt.fill_between(posicion_cv2, np.array(energia_cv2)-np.array(incertidumbre_cv2),np.array(energia_cv2)+np.array(incertidumbre_cv2),alpha=0.2,color='blue')
plana_cv1=buscar_parte_plana(posicion_cv2,'CV2',energia_cv2,incertidumbre_cv2,40,False,True)
plt.show()
plt.close()

################################################################################################################################################
################################################################################################################################################
################################################################################################################################################
def calculo_de_minimos_maximos(array,posicion,CV,incertidumbre,minimo=False,maximo=False,margen=40):
    guardador=100213123
    if maximo==True:
        indice_del_valor_maximo=np.argmax(array[30:-30])
        print(f'Máximos de {CV:s}: (posición,altura)')
        print('Absolutos: ',(posicion[indice_del_valor_maximo]),max(array[30:-30]))
        print('------------------')
        print('Relativos:')
        for i in range(len(posicion)):
            try:
                if i<margen:
                    pass
                else:
                    if array[i]<array[i+1]:
                        continue
                    elif int(array[i])==int(np.mean(array[i-margen:i])) and int(array[i])==int(np.mean(array[i:i+margen])) and int(array[i])==int(array[i+margen+1]):
                        continue
                    elif int(array[i])>int(np.mean(array[i:i+margen])) and int(array[i])>int(np.mean(array[i-margen:i])) and array[i]<np.mean(array[i:i+margen])+incertidumbre[i] and array[i]>np.mean(array[i:i+margen])-incertidumbre[i]:
                        if guardador==round(array[i],0):
                            pass
                        else:
                            print(posicion[i],array[i])
                            guardador=round(array[i],0)
            except IndexError:
                print('------------------')
                print('Fin de la búsqueda')
                print('------------------')
                break
    if minimo==True:
        indice_del_valor_minimo=np.argmin(array[30:-30])
        print(f'Mínimos de {CV:s}: (posición,altura)')
        print('Absolutos: ',(posicion[indice_del_valor_minimo]),min(array[30:-30]))
        print('------------------')
        print('Relativos:')
        for i in range(len(posicion)):
            try:
                if i<margen:
                    pass
                else:
                    if array[i]>array[i+1]:
                        continue
                    elif int(array[i])==int(np.mean(array[i-margen:i])) and int(array[i])==int(np.mean(array[i:i+margen])) and int(array[i])==int(array[i+margen+1]):
                        continue
                    elif int(array[i])<int(np.mean(array[i:i+margen])) and int(array[i])<int(np.mean(array[i-margen:i])) and array[i]<np.mean(array[i:i+margen])+incertidumbre[i] and array[i]>np.mean(array[i:i+margen])-incertidumbre[i]:
                        if guardador==round(array[i],0):
                            pass
                        else:
                            print(posicion[i],array[i])
                            guardador=round(array[i],0)

            except IndexError:
                print('------------------')
                print('Fin de la búsqueda')
                print('------------------')
                break
################################################################################################################################################
################################################################################################################################################
################################################################################################################################################
print('')
print('------------------------------------------------------------')
print('------------------------------------------------------------')
print('Cálculo de la posición y altura de los máximos de la función')
print('------------------------------------------------------------')
print('------------------------------------------------------------')
maximo_cv1=calculo_de_minimos_maximos(energia_cv1,posicion_cv1,'CV1',incertidumbre_cv1,False,True)
maximo_cv2=calculo_de_minimos_maximos(energia_cv2,posicion_cv2,'CV2',incertidumbre_cv2,False,True)
print('')
print('------------------------------------------------------------')
print('------------------------------------------------------------')
print('Cálculo de la posición y altura de los mínimos de la función')
print('------------------------------------------------------------')
print('------------------------------------------------------------')
minimo_cv1=calculo_de_minimos_maximos(energia_cv1,posicion_cv1,'CV1',incertidumbre_cv1,True,False)
minimo_cv2=calculo_de_minimos_maximos(energia_cv2,posicion_cv2,'CV2',incertidumbre_cv2,True,False)
print('')
print('-----------------------------------------------')
print('FIN DEL PROGRAMA')
print('-----------------------------------------------')
################################################################################################################################################
