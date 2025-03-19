from Encoder import steganographic_encoder
from Decoder import steganographic_decoder
import numpy as np
import cv2 as cv
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


class stegLogic():

    def __init__(self):
        self.png = None
        self.integrityFlag = False
        self.identityFlag = False

    def open_image(self,file_path):
        self.png = cv.imread(file_path,cv.IMREAD_COLOR_BGR)
        height, width, channel = self.png.shape
        qformat = QImage.Format.Format_BGR888
        qimg = QImage(self.png.data, width, height, self.png.strides[0], qformat)
        pixmap = QPixmap.fromImage(qimg)
        return pixmap
    
    def update_img(self):
        height, width, channel = self.png.shape
        qformat = QImage.Format.Format_BGR888
        qimg = QImage(self.png.data, width, height, self.png.strides[0], qformat)
        pixmap = QPixmap.fromImage(qimg)
        pixmap = pixmap.scaled(width,height,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        return pixmap
    
    def encodePNG(self,text,password):
        encoder = steganographic_encoder(password,png=self.png)
        self.png = encoder.encode(text,self.integrityFlag,self.identityFlag)
    
    def decodePNG(self,password):
        decoder = steganographic_decoder(password,png=self.png)
        decoder.decode()
        plaintext = decoder.get_plaintext()
        EHash = None
        CHash = None
        if decoder.extracted_hash is not None:
            EHash,CHash = decoder.getHash()
        return plaintext,EHash,CHash
    
    def save_image(self,path):
        cv.imwrite(path, self.png)
    
    def safety_check(self,plaintext):
        if self.png.size*8 < len(plaintext)*8+32+2:
            return False,False
        elif self.png.size*8 < (len(plaintext)*8+256+32+2) and self.integrityFlag: #256-hash 32-header 2-flagy
            return False,False
        elif self.png.size*3 < len(plaintext)*8+32+2: #32-header 2-flagy
            return False,True
        elif self.png.size*3 < (len(plaintext)*8+256+32+2) and self.integrityFlag: #256-hash 32-header 2-flagy
            return False,True
        return True,True