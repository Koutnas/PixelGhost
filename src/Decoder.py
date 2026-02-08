import cv2 as cv
from hashlib import sha256
import numpy as np
import hmac

class steganographic_decoder():

    def __init__(self,password:str,png_path:str=None,png = None):
        self.png_path = png_path              # Cesta k obrázku (volitelné, může být předáno jako NumPy pole)
        self.password = password              # Heslo používané k rekonstrukci pořadí pixelů a ověření identity
        self.decoded_text = ''                # Místo pro výstupní text po dekódování
        self.extracted_identity_sig = None    # Extrahovaný HMAC podpis
        self.extracted_hash = None            # Extrahovaný hash zprávy
        self.headerLenght = 32                # Počet bitů rezervovaný pro hlavičku (velikost zakódované zprávy)
        self.hashLenght = 256                 # Délka SHA-256 v bitech
        self.flagLenght = 2                   # Délka flagu pro určení přítomnosti hash/identity
        self.png = png                        # Obraz jako NumPy pole
    
    def open_img(self): # Načte obrázek ze souboru do NumPy matice
        self.png = cv.imread(self.png_path,cv.IMREAD_COLOR_BGR)
    
    def pixel_order(self): # Vytváří deterministické pořadí pixelů na základě hash hesla
        seed = int(sha256(self.password.encode("UTF-8")).hexdigest(),16) #Seedne random na základě hashe hesla
        rng = np.random.default_rng(seed)
        rows = np.arange(0,self.png.shape[0],1)
        columns = np.arange(0,self.png.shape[1],1)
        rows,columns = np.meshgrid(rows,columns) #https://www.geeksforgeeks.org/numpy-meshgrid-function/
        possible_pos = np.column_stack((rows.ravel(),columns.ravel())) #https://www.geeksforgeeks.org/numpy-column_stack-in-python/ .ravel() ti udělá z 2d matice 1d list
        rng.shuffle(possible_pos)
        return possible_pos
    
    def acces_bit(self,channel_value,bit_position): # Vrátí konkrétní bit z barevného kanálu
        if channel_value & (1<<bit_position):
            return "1"
        else:
            return "0"
    
    def get_plaintext(self):
        return self.decoded_text
    
    def getSignature(self): # Vrací extrahovaný a nově vypočítaný podpis
        return self.extracted_identity_sig,hmac.new(key=self.password.encode('utf-8'),msg=self.decoded_text.encode('utf-8'),digestmod='sha256').hexdigest()
    
    def getHash(self): # Vrací extrahovaný a nově vypočítaný hash
        return self.extracted_hash,sha256(self.decoded_text.encode("UTF-8")).hexdigest()

    def bits_into_plaintext(self,bit_text): # Převede řetězec bitů do klasického stringu
        byte_list = [bit_text[i:i+8] for i in range(0, len(bit_text), 8)]
        plaintext = ''.join(chr(int(char, 2)) for char in byte_list)
        self.decoded_text = plaintext
    
    def bin_to_hex(self,bin): # Převede binární hash/hmac to hexadecimálního formátu
        if bin is not None:
            return hex(int(bin,2))[2:]

    def separate_bitstr(self,plaintext):            # Oddělí flag, hlavičku, hash a podpis od samotného textu
        flag = int(plaintext[-self.flagLenght:],2)  # Získá poslední 2 bity jako flag
        plaintext = plaintext[:-self.flagLenght]    # Odstraní flag z řetězce
        plaintext = plaintext[self.headerLenght:]   # Odstraní hlavičku
        match flag:
            case 0:
                return plaintext,None,None
            case 1:
                hash = plaintext[-self.hashLenght:]
                plaintext = plaintext[:-self.hashLenght]
                return plaintext,hash,None
            case 3:  # 11 
                identity_sig = plaintext[-(self.hashLenght):]
                plaintext = plaintext[:-self.hashLenght]
                hash = plaintext[-self.hashLenght:]
                plaintext = plaintext[:-self.hashLenght]
                return plaintext,hash,identity_sig    

    def decode(self): # Hlavní metoda pro dekódování obrázku
        if self.png_path != None and np.any(self.png) == False: # Pokud obrázek ještě není načtený, načti ho
            self.open_img()
        positions = self.pixel_order() # Pořadí pixelů dle hesla
        header = ""

        for i in range(self.headerLenght): # Extrahuj 32bitovou hlavičku (délka zprávy)
            header = header + self.acces_bit(self.png[positions[i//3,0],positions[i//3,1],i%3],0) #extrakce headru

        if int(header,2) <= self.png.size: # Optimalizace: sníží počet použitých pixelů pokud stačí méně
            if int(header,2)%3 != 0:
                pixels_needed = int(str(int(header,2)/3).split(".")[0])+1
            else:
                pixels_needed = int(int(header,2)/3)
            positions = positions[:pixels_needed]
        
        ctr = 0
        bit_text = ""
        for i in range(int(header,2)//self.png.size + 1): # Extrakce zprávy bit po bitu
            for j in range(self.png.size):
                bit_text += self.acces_bit(int(self.png[positions[j//3,0],positions[j//3,1],j%3]),i)
                ctr += 1
                if ctr == int(header,2):
                    break

        text, hash, identity_sig = self.separate_bitstr(bit_text) # Odděl text, hash, podpis

        self.bits_into_plaintext(text)                                  # Převod bitů na text
        self.extracted_hash = self.bin_to_hex(hash)                     # Uložení extrahovaného hashe
        self.extracted_identity_sig = self.bin_to_hex(identity_sig)     # Uložení extrahovaného Hmacu
