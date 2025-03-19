import cv2 as cv
from hashlib import sha256
import numpy as np


class steganographic_encoder():
    
    def __init__(self,password:str,png_path:str=None,png = None):
        self.png_path = png_path
        self.password = password
        self.headerLenght = 32 #bity dedikované ze začátku k uložení informace o délce celé zprávy
        self.png = png
    
    def open_img(self):
        self.png = cv.imread(self.png_path,cv.IMREAD_COLOR_BGR)

    def slice_text(self,plaintext):
        arr = np.array(list(plaintext))
        result = ["".join(arr[i:i+self.png.size]) for i in range(0, len(arr), self.png.size)]
        return result
    
    def integrity_insurance(self,plaintext):
        hash = bin(int(sha256(plaintext.encode("UTF-8")).hexdigest(),16))[2:]
        for i in range(256 - len(hash)):
            hash = "0"+hash
        return hash

    def pixel_shuffle(self,plaintext):
        seed = int(sha256(self.password.encode("UTF-8")).hexdigest(),16) #Seedne random na základě hashe hesla
        rng = np.random.default_rng(seed)
        rows = np.arange(0,self.png.shape[0],1)
        columns = np.arange(0,self.png.shape[1],1)

        rows,columns = np.meshgrid(rows,columns) #https://www.geeksforgeeks.org/numpy-meshgrid-function/

        possible_pos = np.column_stack((rows.ravel(),columns.ravel())) #https://www.geeksforgeeks.org/numpy-column_stack-in-python/ .ravel() ti udělá z 2d matice 1d list
        rng.shuffle(possible_pos)

        pixels_needed = 0
        if len(plaintext) >= self.png.size:
            return possible_pos
        if len(plaintext)%3 != 0:
            pixels_needed = int(str(len(plaintext)/3).split(".")[0])+1
        else:
            pixels_needed = int(len(plaintext)/3)
        possible_pos = possible_pos[:pixels_needed]
        return possible_pos
    
    def encode_bit(self,channel_value,bit,bit_position):
        if int(bit):
            return channel_value | (1<<bit_position)
        else:
            return channel_value & ~(1<<bit_position)

    def str_into_bitstr(self,plaintext):
        bitstr = ""
        for i in bytearray(plaintext, encoding ='utf-8'):
            bitstr = bitstr + (format(i, '08b'))
        return bitstr
    
    def add_header(self,bin_plaintext): #vraci velikost zpravy
        header = bin(len(bin_plaintext)+self.headerLenght)[2:]
        for i in range(self.headerLenght - len(header)):
            header = "0"+header
        bin_plaintext = header+bin_plaintext
        return bin_plaintext
    
    def safety_check(self,bin_plaintext):
        if len(bin_plaintext) >= 2**(self.headerLenght) or len(bin_plaintext) > self.png.size*8:
            print("Too long string to encode")
            return False
        else:
            return True
        
    def encode(self,plaintext,hashFlag,identFlag):
        if self.png_path != None and np.any(self.png) == False:
            self.open_img()
        
        if hashFlag:
            hash = self.integrity_insurance(plaintext)
            bitstr = self.str_into_bitstr(plaintext)
            bitstr = self.add_header(bitstr+hash+"01")
        
        elif hashFlag and identFlag:

            pass #To be implemented
        
        else:
            bitstr = self.str_into_bitstr(plaintext)
            bitstr = self.add_header(bitstr+"00")

        if self.safety_check(bitstr):
            positions = self.pixel_shuffle(bitstr)
            plaintext_slices = self.slice_text(bitstr)

            for i in range(len(plaintext_slices)):
                for j,bit in enumerate(plaintext_slices[i]):
                    self.png[positions[j//3,0],positions[j//3,1],j%3] = self.encode_bit(int(self.png[positions[j//3,0],positions[j//3,1],j%3]),bit,i)
            return self.png
            
        




        