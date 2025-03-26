import customtkinter
import socket
import subprocess
import concurrent.futures
import re

""" Dictionnaire permettant de recueillir les hosnames des machines connectées
    sur un réseau """
host = {}
# Timeout pour socket (éviter les blocages)
socket.setdefaulttimeout(1)


"""=============== Classes d'interface ====================="""
class FrameHautGauche(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.lblRacineIp = customtkinter.CTkLabel(master=self, text="Racine IP à scanner", fg_color="transparent", height=10)
        self.lblRacineIp.grid(row=0, column=0, padx=10, pady=5, sticky="nw")
        self.txtRacineIp = customtkinter.CTkTextbox(master=self,corner_radius=5,height=20)
        self.txtRacineIp.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.txtRacineIp.insert("0.0", "192.168.10")

class FrameHautDroite(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.textbox = customtkinter.CTkTextbox(master=self, corner_radius=5,wrap="word")
        self.textbox.grid(row=0, column=0 , padx=10, pady=10, sticky="nsew")
        self.textbox.insert("0.0", "Veuillez lancer le scan avec les paramètres souhaités")

"""================ Classes techniques ===================== """

class ScanAdressesIP():

    """ Constructeur de la classe prend en argument les paramètres suivants: """
    """ address : adresse IP à scanner                                       """
    def __init__(self, address):

        self.address = address

    def ping(self,ip):
        """ Vérifie si une IP répond au ping avant de la scanner """
        try:
            # Sur Windows : utiliser 'ping -n 1'
            # Sur Linux/Mac : utiliser 'ping -c 1'
            result = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.returncode == 0  # True si l'IP est active
        except Exception:
            return False
        


    """ Méthode de classe permettant de récupérer le hostname du périphérique           """
    """ connecté au réseau. Elle prend en paramètre la variable de classe représentant """
    """ l'adresse IP à recherchée                                                       """
    def ScanAdresseIP(self, address):
        global host

        """ Essaye de résoudre l'IP en hostname si elle répond au ping """
        if not self.ping(self.address):  # Évite les IP inactives
            host[self.address] = None
        else:

            """ On gère l'exception en cas de périphérique non connecté à l'adresse IP à scanner """
            try:
                """ On récupère le hostname et l'alias de la machine connectée """
                hostname, alias, _ = socket.gethostbyaddr(address)
                """ On associe le hostname à l'adresse IP et on les sauve dans le dictionnaire """
                host[address] = hostname
            except socket.herror:
                host[address] = None

"""================ Classe application ===================== """

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Scanner réseau")
        self.geometry("800x300")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.FrameHautGauche = FrameHautGauche(self)
        self.FrameHautGauche.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.FrameHautDroite = FrameHautDroite(self)
        self.FrameHautDroite.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew")

        # Barre de progression
        self.progressbar = customtkinter.CTkProgressBar(self,height=20, progress_color=('chartreuse2', 'chartreuse4'))
        self.progressbar.grid(row=1, column=0, padx=10, pady=10, columnspan=2, sticky="ew")
        self.progressbar.set(0)  # Initialiser à 0%   

        self.oBouton = customtkinter.CTkButton(self, text="Scanner le réseau", fg_color='chartreuse4', hover_color="dark green", command=self.oBouton_Clic)
        self.oBouton.grid(row=2, column=0, padx=20, pady=10, sticky="ew", columnspan=2)

        
    def oBouton_Clic(self):
        sResultatScan=""
        addresses = []
        self.FrameHautDroite.textbox.delete("0.0", "end")
        self.FrameHautDroite.textbox.insert("0.0", "===== Début du scan ===== \n")
        self.FrameHautDroite.textbox.update_idletasks()

        """ On définit une plage d'adresses IP à scanner à partir de la chaine saisie par l'utilisateur""" 
        # Regex pour valider la racine IP saisie par l'utilisateur
        regex_racine_ip = r"^((25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.){2}(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)$"

        if re.match(regex_racine_ip, self.FrameHautGauche.txtRacineIp.get("0.0", "end")) :
            for ping in range(1, 255):
                addresses.append("192.168.10." + str(ping))

            iNombreAdresses = len(addresses)

            # Utilisation de ThreadPoolExecutor pour exécuter en parallèle
            results = []
            max_threads = 40
            with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
                futures = {executor.submit(ScanAdressesIP(address).ScanAdresseIP, address) for address in addresses}  
                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    future.result()  # Exécute les scans

                    # Mise à jour de la barre de progression
                    progress = i / iNombreAdresses
                    self.progressbar.set(progress)
                    self.progressbar.update_idletasks()        

            """ On affiche le résultat qui affiche pour chaque machine connectée son nom d'hôte """
            for address, hostname in host.items():
                if (hostname != None): 
                    print(address, '=>', hostname)
                    sResultatScan += address + " => " + hostname  + "\n"

            
            self.FrameHautDroite.textbox.insert("end", sResultatScan + "\n")
        else:
            # L'utilisateur a fait une erreur de saisie dans la racine ip : on l'indique
             self.FrameHautDroite.textbox.insert("end", ">>>> Erreur : Veuillez renseigner une racine ip valide, de la forme 192.168.10 (sans le dernier '.' ni le dernier chiffre)\n")
        self.FrameHautDroite.textbox.insert("end", "===== Fin du scan ======")
        

app = App()
app.mainloop()