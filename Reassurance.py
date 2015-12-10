## Importation des packages
import csv
import numpy


# Paramètres

# Age minimum des tables
age_min = 40

# Taux technique
taux_technique = 0.0125

# Paramètres réassureur
ch_reass = 0.15
ch_secu = 0.0763
ab_reass = 1

# Importation de la table de tarification des valides
table_val = numpy.empty((0,3), float)
with open('I:\\Test\\Taux_val.csv', newline = '') as f:
    reader = csv.reader(f, delimiter = ';')
    for row in reader:
        table_val = numpy.concatenate((table_val,numpy.array([row], float)), axis = 0)

# Importation de la table de tarification des dépendants partiels
table_dep_par = numpy.empty((0,3), float)
with open('I:\\Test\\Taux_dep_par.csv', newline = '') as f:
    reader = csv.reader(f, delimiter = ';')
    for row in reader:
        table_dep_par = numpy.concatenate((table_dep_par,numpy.array([row], float)), axis = 0)

# Importation de la table de tarification des dépendants totaux
table_dep_tot = numpy.empty((0,3), float)
with open('I:\\Test\\Taux_dep_tot.csv', newline = '') as f:
    reader = csv.reader(f, delimiter = ';')
    for row in reader:
        table_dep_tot = numpy.concatenate((table_dep_tot,numpy.array([row], float)), axis = 0)


## Définition des classes

# Classe Table de tarification par état
class TableTarifEtat:

    # Constructeur
    def __init__(self, table, age_min, taux_tech):
        self.table = table
        self.age_min = age_min
        self.age_max = table.shape[0] + age_min - 1
        self.taille = self.age_max - age_min + 1
        self.taux_tech = float(taux_tech)
        self.taux_actu = float(1 / (1 + taux_tech))
        self.shape = table.shape
        self.q = table[:,0:1]
        self.i_sup = table[:,1:2]
        self.i_spe = table[:,2:3]
        self.p = 1 - (self.q + self.i_sup + self.i_spe)

    # Méthode lx
    def l(self):
        sortie = numpy.empty((self.taille,1), float)
        sortie[0] = 100000
        for i in range(1, self.taille):
            sortie[i] = sortie[i - 1] * self.p[i - 1]
        return sortie

    # Méthode Table d'actualisation
    def table_actu(self, coeff):
        sortie = self.taux_actu * numpy.ones((self.taille, 1))
        for i in range(0, self.taille):
            sortie[i] = sortie[i]**(self.age_min + i + coeff)
        return sortie

    # Méthode Dx
    def D(self):
        return self.l() * self.table_actu(0)

    # Méthode Nx
    def N(self):
        sortie = numpy.zeros(self.taille)
        for i in range(0, self.taille):
            for j in range(i, self.taille):
                sortie[i] = sortie[i] + self.D()[j]
        return sortie

    # Méthode Dx_sup
    def D_sup(self):
        return self.l() * self.table_actu(0.5) * self.i_sup

    # Méthode Dx_spe
    def D_spe(self):
        return self.l() * self.table_actu(0.5) * self.i_spe

    # Méthode Nx_sup
    def N_sup(self):
        sortie = numpy.zeros(self.taille)
        for i in range(0, self.taille):
            for j in range(i, self.taille):
                sortie[i] = sortie[i] + self.D_sup()[j]
        return sortie

    # Méthode Nx_spe
    def N_spe(self):
        sortie = numpy.zeros(self.taille)
        for i in range(0, self.taille):
            for j in range(i, self.taille):
                sortie[i] = sortie[i] + self.D_spe()[j]
        return sortie

    # Méthode ax
    def a(self, age, duree, carence, decalage, differe):
        return (self.N()[age + carence + decalage + differe : ] / self.D()[age + carence + decalage : - differe].T).T

    # Méthode Ex (capital différé de changement dans l'état supérieur)
    def E_sup(self, age, duree, carence, decalage, differe):
        return (self.D_sup()[age + carence : - decalage - differe ] / self.D()[age + duree]).T

    # Méthode Ex (capital différé de changement dans l'état supérieur - supérieur)
    def E_spe(self, age, duree, carence, decalage, differe):
        return (self.D_spe()[age + carence : - decalage - differe] / self.D()[age + duree]).T

# Classe Table de tarification
class Tarif:

    # Constructeur
    def __init__(self, table_val, table_dep_par, table_dep_tot, age_min, taux_tech):
        self.va = TableTarifEtat(table_val, age_min, taux_tech)
        self.dp = TableTarifEtat(table_dep_par, age_min, taux_tech)
        self.dt = TableTarifEtat(table_dep_tot, age_min, taux_tech)
        self.age_min = age_min
        self.taille = self.va.taille
        self.taux_tech = taux_tech

# Classe Assuré
class Assure:

    # Constructeur
    def __init__(self, age, duree, duree_primes, freq_primes):
        self.age = age
        self.duree = duree
        self.duree_primes = duree_primes
        self.freq_primes = freq_primes

# Classe Engagements
class Engagements(Tarif, Assure):

    # Constructeur
    def __init__(self, tarif, assure):
        Tarif.__init__(self, tarif.va.table, tarif.dp.table, tarif.dt.table, tarif.age_min, tarif.taux_tech)
        Assure.__init__(self, assure.age, assure.duree, assure.duree_primes, assure.freq_primes)
        self.tarif = tarif
        self.assure = assure
        self.age_table = self.age - self.age_min

    # Méthode Rente en dépendance totale
    def ren_dep_tot(self, duree, carence, decalage, differe):
        return numpy.dot(self.va.E_spe(self.age_table, duree, carence, decalage, differe), \
                         self.dt.a(self.age_table, duree, carence, decalage, differe))

    # Méthode Exonération
    def exo(self, duree, carence, decalage,differe):
        return

    # Méthode Engagement
    def eng(self, gar, duree):

        car0, car1, car2, car3 = 0, 0, 0, 0

        if duree == 0:
            car0 = (1 - 0.5 - 0.35) * eval('self.' + gar + '(0, 0, 1, 1)')
            car1 = 0.5 * eval('self.' + gar + '(0, 1, 1, 1)')
            car3 = 0.35 * eval('self.' + gar + '(0, 3, 1, 1)')

        elif duree == 1:
            car1 = (1 - 0.35) * eval('self.' + gar + '(1, 1, 1, 1)')
            car3 = 0.35 * eval('self.' + gar + '(1, 3, 1, 1)')

        elif duree == 2:
            car2 = (1 - 0.35) * eval('self.' + gar + '(2, 2, 1, 1)')
            car3 = 0.35 * eval('self.' + gar + '(2, 3, 1, 1)')

        else:
            car3 = eval('self.' + gar + '(' + str(duree) + ',' + str(duree) + ', 1, 1)')

        return car0 + car1 + car2 + car3

# Classe Réassureur
class Reassureur:

    # Constructeur
    def __init__(self, ch_reass, ch_secu, ab_reass):
        self.ch_reass = ch_reass
        self.ch_secu = ch_secu
        self.ab_reass = ab_reass
        self.ch_r = (1 + self.ch_secu) * (1 - self.ch_reass)

# Classe Primes
class Primes(Engagements, Reassureur):

    # Constructeur
    def __init__(self, eng, reass):
        Engagements.__init__(self, eng.tarif, eng.assure)
        Reassureur.__init__(self, reass.ch_reass, reass.ch_secu, reass.ab_reass)

    # Méthode Primes Pures
    def p_pures(self, gar):
        return self.ch_r * self.ab_reass * self.eng(gar, 0)

## Instanciation des paramètres
Test = Tarif(table_val, table_dep_par, table_dep_tot, age_min, taux_technique)
Client = Assure(50, 1, 0, 1)
SwissRe = Reassureur(ch_reass, ch_secu, ab_reass)
E = Engagements(Test, Client)
P = Primes(E, SwissRe)
print(P.p_pures('ren_dep_tot'))


