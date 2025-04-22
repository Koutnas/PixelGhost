from PyQt6.QtWidgets import QWidget, QPushButton, QLabel,QApplication,QHBoxLayout,QGridLayout, QLineEdit,QTextEdit,QCheckBox,QSizePolicy,QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QImage, QPixmap
from Stegui_logic import stegLogic # vlastní logika
import numpy as np
import sys

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()              # Inicializace UI prvků
        self.logic = stegLogic()    # Vytvoření instance logiky

    def init_ui(self):
        self.setWindowTitle("Steganography") # Titulek okna
        self.setGeometry(250, 250, 800, 500) # Rozměry okna
        self.switch = True                   # True = encode režim
        parentLayout = QGridLayout()         # Hlavní rozložení
        topLeftLayout = QHBoxLayout()        # Rozložení vlevo nahoře (přepínač režimu)
        topRightLayout = QHBoxLayout()       # Rozložení vpravo nahoře (Load/Save)
        
        # Přepínač režimu + popisek
        self.mode_button = QPushButton("Switch mode", self)
        self.mode_button.clicked.connect(self.switch_mode)
        self.mode_label = QLabel("Encode")

        # Tlačítka Load/Save
        self.load_button = QPushButton("Load",self)
        self.load_button.clicked.connect(self.load_image)
        self.save_button = QPushButton("Save",self)
        self.save_button.clicked.connect(self.save_image)

        # Label pro zobrazení obrázku
        self.image_label = QLabel("load image to proceed", self)
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setMinimumSize(100, 100)

        self.dynamicLayout = QGridLayout() # Dynamická část layoutu co se mění za běhu programu
        self.encode_layout()               # Defaultně se zobrazí encode layout

        # Umístění widgetů do layoutů
        topLeftLayout.addWidget(self.mode_button)
        topLeftLayout.addWidget(self.mode_label)
        
        topRightLayout.addWidget(self.load_button)
        topRightLayout.addWidget(self.save_button)
        
        parentLayout.addLayout(topLeftLayout,0,0)
        parentLayout.addLayout(topRightLayout,0,1)
        parentLayout.addWidget(self.image_label,1,1,alignment=Qt.AlignmentFlag.AlignCenter)
        parentLayout.addLayout(self.dynamicLayout,1,0)

        parentLayout.setColumnStretch(0,1)
        parentLayout.setColumnStretch(1,1)

        self.setLayout(parentLayout)

    def encode_layout(self):
        # Nastavení rozhraní pro režim "encode"
        self.clear_layout()
        self.mode_label.setText("Encode")
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter message to encode")
            
        self.password_inE = QLineEdit()
        self.password_inE.setPlaceholderText("Enter password")
        self.encode_button = QPushButton("Encode",self)
        self.encode_button.clicked.connect(self.encode_into_image)

        self.integrity_checkbox = QCheckBox(text="Integrity verification")
        self.integrity_checkbox.stateChanged.connect(self.integrity_condition)
        self.identity_checkbox = QCheckBox(text="Identity verification")
        self.identity_checkbox.stateChanged.connect(self.identity_condition)
        self.identity_checkbox.setEnabled(False)

        # Přidání widgetů do dynamického layoutu
        self.dynamicLayout.addWidget(self.text_input,0,0,1,2)
        self.dynamicLayout.addWidget(self.password_inE,1,0)
        self.dynamicLayout.addWidget(self.encode_button,1,1)
        self.dynamicLayout.addWidget(self.integrity_checkbox,2,0)
        self.dynamicLayout.addWidget(self.identity_checkbox,3,0)
    
    def decode_layout(self):
        # Rozhraní pro dekódování
        self.mode_label.setText("Decode")
        self.clear_layout()
        self.text_display = QTextEdit()
        self.text_display.setPlaceholderText("Nothing decoded yet...")
        self.text_display.setReadOnly(True)

        self.password_inD = QLineEdit()
        self.password_inD.setPlaceholderText("Enter password")
        self.decode_button = QPushButton("Decode",self)
        self.decode_button.clicked.connect(self.decode_from_image)

        self.intLabel = QLabel("Integrity check: ")
        self.idLabel = QLabel("Identity check: ")

        self.dynamicLayout.addWidget(self.text_display,0,0,1,2)
        self.dynamicLayout.addWidget(self.password_inD,1,0)
        self.dynamicLayout.addWidget(self.decode_button,1,1)
        self.dynamicLayout.addWidget(self.intLabel,2,0)
        self.dynamicLayout.addWidget(self.idLabel,3,0)

    def clear_layout(self):
        # Vymaže dynamický layout
        if self.dynamicLayout:
            while self.dynamicLayout.count():
                item = self.dynamicLayout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
    
    def switch_mode(self):
        # Přepne režim Encode/Decode
        if self.switch == False:
            self.switch = True
            self.encode_layout()
        else:
            self.switch = False
            self.decode_layout()
    
    def integrity_condition(self,state):
        # Aktivace integrity -> aktivuje volitelně identitu
        self.identity_checkbox.setEnabled(state == 2)
        self.identity_checkbox.setChecked(False)
        match state:
            case 2:
                self.logic.integrityFlag = True
            case 0:
                self.logic.integrityFlag = False

    def identity_condition(self, state):
        # Zapnutí identity flagu
        match state:
            case 2:
                self.logic.identityFlag = True
            case 0:
                self.logic.identityFlag = False

    def load_image(self):
        # Načtení obrázku z disku
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png)")
        if not file_path:
            return
        pixmap = self.logic.open_image(file_path)
        self.image_label.setPixmap(pixmap)
    
    def encode_into_image(self):
        # Zašifrování textu do obrázku
        if not np.any(self.logic.png):
            return
        text = self.text_input.toPlainText()
        if text == "":
            return
        password = self.password_inE.text()
        if password == "":
            return
        
        safe,possible = self.logic.safety_check(text)
        if not safe and possible:
            result = self.raise_warning()
            if result == QMessageBox.StandardButton.No:
                return
        if not safe and not possible:
            self.raise_ultimatum()    
            return
        
        self.logic.encodePNG(text,password)
        pixmap = self.logic.update_img()
        self.image_label.setPixmap(pixmap)
        self.text_input.clear()
    
    def decode_from_image(self):
        # Rozšifrování textu z obrázku
        self.text_display.clear()
        if not np.any(self.logic.png):
            return
        password = self.password_inD.text()
        if password == "":
            return
        
        text, EHash, CHash, ESig, CSig = self.logic.decodePNG(password)
        self.text_display.setText(text)

        # Zobrazení výsledků integrity a identity
        if EHash is not None:
            self.intLabel.setText("Integrity check: "+EHash[:16]+"... == "+CHash[:16]+"... : "+str(CHash==EHash))
            if ESig is not None:
                self.idLabel.setText("Identity check: " + (ESig[:16]+"... == "+CSig[:16]+"... : "+str(CSig==ESig)))
            else:
                self.idLabel.setText("Identity check: N/A")     
        else:
            self.intLabel.setText("Integrity check: N/A")

    def save_image(self):
        # Uložení obrázku
        if self.logic.png is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);")
        if not file_path:
            return
        self.logic.save_image(file_path)

    def raise_warning(self):
        #Varování pokud je zde více dat než kolik jsme schopni skrýt do daného obrázku
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirm Action")
        msg_box.setText("Message is too long for undetectable encoding, proceeding will cause visual fragments, do you still wish to proceed?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)  # Default to "No"
        result = msg_box.exec()
        return result
    
    def raise_ultimatum(self):
        #Upozorní uživatele že je zde moc textu na to aby se vůbec vešel do obrázku
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText("Amount of text you want to encode is larger than there is space avalible in the whole picture. \nOperation cannot proceed.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def resizeEvent(self,event):
        # Dynamické přepočítávání obrázku při změně velikosti UI
        if self.logic.png is None:
            return
        pixmap = self.logic.update_img()
        self.image_label.setPixmap(pixmap)
        super().resizeEvent(event)

app = QApplication(sys.argv)
window = MainUI()
window.show()
sys.exit(app.exec())