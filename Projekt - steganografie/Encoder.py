import cv2 as cv
from hashlib import sha256
import numpy as np
import hmac #https://docs.python.org/3/library/hmac.html


class steganographic_encoder():
    
    def __init__(self,password:str,png_path:str=None,png = None):
        self.png_path = png_path    # Cesta k obrázku
        self.password = password    # Heslo pro seedování a podpis
        self.headerLenght = 32      # Bity dedikované ze začátku k uložení informace o délce celé zprávy
        self.png = png              # Načtený obrázek (v případě, že není poskytována cesta)
    
    def open_img(self):
        self.png = cv.imread(self.png_path,cv.IMREAD_COLOR_BGR)

    def slice_text(self,plaintext): # Rozdělí text na části o velikosti rovné počtu pixelů (kanálů) v obrázku
        arr = np.array(list(plaintext))
        result = ["".join(arr[i:i+self.png.size]) for i in range(0, len(arr), self.png.size)]
        return result
    
    def integrity_insurance(self,plaintext): # Vytvoří hash zprávy pro kontrolu integrity
        hash = bin(int(sha256(plaintext.encode("UTF-8")).hexdigest(),16))[2:]
        for i in range(256 - len(hash)):
            hash = "0"+hash
        return hash
    
    def create_identity_signature(self, plaintext): # Vytvoří HMAC podpis zprávy pro ověření identity
        signature = hmac.new(key=self.password.encode('utf-8'),msg=plaintext.encode('utf-8'),digestmod='sha256').hexdigest()  
        bin_sig = bin(int(signature, 16))[2:]
        while len(bin_sig) < 256:
            bin_sig = "0" + bin_sig
        return bin_sig


    def pixel_shuffle(self,plaintext): # Vygeneruje náhodné pozice pro zakódování bitů na základě hash hesla
        
        seed = int(sha256(self.password.encode("UTF-8")).hexdigest(),16)
        rng = np.random.default_rng(seed)
        
        rows = np.arange(0,self.png.shape[0],1)
        columns = np.arange(0,self.png.shape[1],1)
        rows,columns = np.meshgrid(rows,columns) #https://www.geeksforgeeks.org/numpy-meshgrid-function/
        possible_pos = np.column_stack((rows.ravel(),columns.ravel())) #https://www.geeksforgeeks.org/numpy-column_stack-in-python/ .ravel() ti udělá z 2d matice 1d list
        
        rng.shuffle(possible_pos) # Zamíchá seznam pozic

        pixels_needed = 0
        pixels_needed = (len(plaintext) + 2) // 3  # zaokrouhlení nahoru
        possible_pos = possible_pos[:pixels_needed] # Optimalizace v případě že nejsou potřeba všechny pixely
        return possible_pos
    
    def encode_bit(self,channel_value,bit,bit_position):
        # Zakóduje daný bit na konkrétní pozici v kanálové hodnotě
        if int(bit):
            return channel_value | (1<<bit_position) # nastaví bit na 1
        else:
            return channel_value & ~(1<<bit_position) # nastaví bit na 0

    def str_into_bitstr(self,plaintext): # Převod stringu do bitového řetězce
        bitstr = ""
        for i in bytearray(plaintext, encoding ='utf-8'):
            bitstr = bitstr + (format(i, '08b'))
        return bitstr
    
    def add_header(self,bin_plaintext): # Přidá hlavičku (délka zprávy + hlavička)
        header = bin(len(bin_plaintext)+self.headerLenght)[2:]
        for i in range(self.headerLenght - len(header)):
            header = "0"+header
        bin_plaintext = header+bin_plaintext
        return bin_plaintext
    
    def safety_check(self,bin_plaintext): # Zkontroluje, zda se zpráva vejde do obrázku
        if len(bin_plaintext) >= 2**(self.headerLenght) or len(bin_plaintext) > self.png.size*8:
            print("Too long string to encode")
            return False
        else:
            return True
        
    def encode(self,plaintext,hashFlag,identFlag): # Hlavní funkce pro zakódování zprávy do obrázku
        if self.png_path != None and np.any(self.png) == False:
            self.open_img()
        # Sestavení finální zprávy
        if hashFlag and not identFlag: 
            hash = self.integrity_insurance(plaintext)
            bitstr = self.str_into_bitstr(plaintext)
            bitstr = self.add_header(bitstr+hash+"01") # přidá indikátor integrita ano, identita ne
        
        elif hashFlag and identFlag:
            hash = self.integrity_insurance(plaintext)
            identity_sig = self.create_identity_signature(plaintext)
            bitstr = self.str_into_bitstr(plaintext)
            bitstr = self.add_header(bitstr + hash + identity_sig + "11") # integrita i identita
        
        else:
            bitstr = self.str_into_bitstr(plaintext)
            bitstr = self.add_header(bitstr+"00") # bez integritní nebo autentizační kontroly

        if self.safety_check(bitstr):
            positions = self.pixel_shuffle(bitstr)
            plaintext_slices = self.slice_text(bitstr)

            # Vkládání bitů do pixelů
            for i in range(len(plaintext_slices)):
                for j,bit in enumerate(plaintext_slices[i]):
                    row = positions[j//3, 0]
                    col = positions[j//3, 1]
                    channel = j % 3
                    current_val = self.png[row, col, channel]
                    self.png[row, col, channel] = self.encode_bit(int(current_val), bit, i)
            return self.png
        