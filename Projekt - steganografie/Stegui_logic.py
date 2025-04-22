from Encoder import steganographic_encoder
from Decoder import steganographic_decoder
import numpy as np
import cv2 as cv
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

# Třída co vše slepuje dohromady
class stegLogic():
    def __init__(self):
        self.png = None
        self.integrityFlag = False
        self.identityFlag = False

    def open_image(self,file_path):
        # Načtení obrázku pomocí OpenCV
        self.png = cv.imread(file_path,cv.IMREAD_COLOR_BGR)
        height, width, channel = self.png.shape
        qformat = QImage.Format.Format_BGR888
        qimg = QImage(self.png.data, width, height, self.png.strides[0], qformat)
        pixmap = QPixmap.fromImage(qimg)
        return pixmap
    
    def update_img(self):
        # Přepočítání obrázku pro zobrazení
        height, width, channel = self.png.shape
        qformat = QImage.Format.Format_BGR888
        qimg = QImage(self.png.data, width, height, self.png.strides[0], qformat)
        pixmap = QPixmap.fromImage(qimg)
        pixmap = pixmap.scaled(width,height,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        return pixmap
    
    def encodePNG(self,text,password):
        # zakódování textu do PNG
        encoder = steganographic_encoder(password,png=self.png)
        self.png = encoder.encode(text,self.integrityFlag,self.identityFlag)
    
    def decodePNG(self,password):
        # Dekódování z PNG
        decoder = steganographic_decoder(password,png=self.png)
        decoder.decode()
        plaintext = decoder.get_plaintext()
        EHash = None
        CHash = None
        ESig= None
        CSig = None
        if decoder.extracted_hash is not None:
            EHash,CHash = decoder.getHash()
        if self.identityFlag:
            ESig,CSig = decoder.getSignature()
        return plaintext,EHash,CHash,ESig,CSig
    
    def save_image(self,path):
        # Uložení obrázku na disk
        cv.imwrite(path, self.png)
    
    def safety_check(self,plaintext):
        # Ověření, zda se text vejde (s přihlédnutím k příznakům)
        bits_needed = len(plaintext)*8
        min_bits = 32 + 2  # header + flagy
        hash_bits = 256 if self.integrityFlag else 0
        sig_bits = 256 if self.identityFlag else 0
        total_bits = bits_needed + min_bits + hash_bits + sig_bits

        if self.png.size * 8 > total_bits:
            if self.png.size * 3 > total_bits:
                return True, True  # text se nevejde vůbec
            return False, True  # text se vejde, ale budou viditelné fragmenty
        return False, False  # v pořádku