import cv2 as cv
from hashlib import sha256
import numpy as np

class steganographic_decoder():

    def __init__(self,password:str,png_path:str=None,png = None):
        self.png_path = png_path
        self.password = password
        self.decoded_text = ''
        self.extracted_hash = ''
        self.headerLenght = 32
        self.hashLenght = 256
        self.png = png
    
    def open_img(self):
        self.png = cv.imread(self.png_path,cv.IMREAD_COLOR_BGR)
    
    def pixel_order(self):
        seed = int(sha256(self.password.encode("UTF-8")).hexdigest(),16) #Seedne random na základě hashe hesla
        rng = np.random.default_rng(seed)
        rows = np.arange(0,self.png.shape[0],1)
        columns = np.arange(0,self.png.shape[1],1)

        rows,columns = np.meshgrid(rows,columns) #https://www.geeksforgeeks.org/numpy-meshgrid-function/

        possible_pos = np.column_stack((rows.ravel(),columns.ravel())) #https://www.geeksforgeeks.org/numpy-column_stack-in-python/ .ravel() ti udělá z 2d matice 1d list
        rng.shuffle(possible_pos)
        return possible_pos
    
    def acces_bit(self,channel_value,bit_position):
        if channel_value & (1<<bit_position):
            return "1"
        else:
            return "0"
    
    def verify_integrity(self):

        text_hash = sha256(self.decoded_text.encode("UTF-8")).hexdigest()
        if self.extracted_hash == text_hash:
            return True
        else:
            return False
    
    def get_plaintext(self):
        return self.decoded_text

    def bits_into_plaintext(self,bit_text):
        byte_list = [bit_text[i:i+8] for i in range(0, len(bit_text), 8)] #https://www.geeksforgeeks.org/convert-binary-to-string-using-python/
        plaintext = ''.join(chr(int(char, 2)) for char in byte_list)
        self.decoded_text = plaintext
    
    def bin_to_hex_hash(self,bin_hash):
        self.extracted_hash = hex(int(bin_hash,2))[2:]

    def separate_bitstr(self,plaintext):
        plaintext = plaintext[self.headerLenght:]
        hash = plaintext[-self.hashLenght:]
        plaintext = plaintext[:-self.hashLenght]
        return plaintext,hash

    def decode(self):
        if self.png == None and self.png_path != None:
            self.open_img()
        else:
            print("There was a problem with opening image")
            return
        positions = self.pixel_order()
        header = ""

        for i in range(self.headerLenght):
            header = header + self.acces_bit(self.png[positions[i//3,0],positions[i//3,1],i%3],0) #extrakce headru
        print(int(header,2))

        if int(header,2) <= self.png.size: #optimalizace v případě že je využito méně než celé rozlišení obrázku
            if int(header,2)%3 != 0:
                pixels_needed = int(str(int(header,2)/3).split(".")[0])+1
            else:
                pixels_needed = int(int(header,2)/3)
            positions = positions[:pixels_needed]
        print("passed")
        ctr = 0
        bit_text = ""
        for i in range(int(header,2)//self.png.size + 1):
            for j in range(self.png.size):
                bit_text =bit_text + self.acces_bit(int(self.png[positions[j//3,0],positions[j//3,1],j%3]),i)
                ctr = ctr + 1
                if ctr == int(header,2):
                    break
        text,hash = self.separate_bitstr(bit_text)

        self.bits_into_plaintext(text)
        self.bin_to_hex_hash(hash)
        


steg_dec = steganographic_decoder("heslo","decoding_test.png")
steg_dec.decode()
print(steg_dec.get_plaintext())
print(steg_dec.verify_integrity())
