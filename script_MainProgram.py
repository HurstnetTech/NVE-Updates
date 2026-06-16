from PyQt6 import QtWidgets, QtGui, QtCore #PyQt Import

from ui_MainUIWindow import Ui_NVE2POINT0 #UI Imports
from ui_FirstSetupWindow import Ui_MainWindow
from ui_WriteMessagesWindow import Ui_WriteMessages
from ui_ProgressPopup import Ui_ProgressWindow
from ui_StandardScrollScreen import Ui_ViewTurn
from ui_Settings import Ui_Settings
from ui_ItemLibrary import Ui_ItemLibrary
from ui_ClassOrdering import Ui_ClassOrdering
from ui_CreatureLibrary import Ui_Creatures
from ui_SkillsLibrary import Ui_SkillsLibrary

import sys #Other Imports
import numpy as np
import math
import time
import shutil
import os
import subprocess
import ctypes
import traceback
import re
from datetime import datetime
import ctypes
import requests
import webbrowser
import struct
import paramiko
import zipfile
import json
import script_Connection
from collections import deque
from script_crypto_utils import encrypt_bytes, decrypt_bytes
import secure_key
import hashlib

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------FIRST Setup--------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

class LabelClick(QtCore.QObject):
    """Event filter to detect when the folder icon is clicked in first setup page 2. Create a file dialog for the user to choose a path, and update the text_edit with the path."""
    
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
    
    def eventFilter(self, obj, event):
        if obj.__class__ == QtWidgets.QLabel and event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                folder = QtWidgets.QFileDialog.getExistingDirectory(obj, "Select Folder")
                self.text_edit.setText(folder)
            return True
        return super().eventFilter(obj, event)

class FirstSetup(QtWidgets.QMainWindow, Ui_MainWindow):
    """Create and handle the first setup application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application using the First Setup script, change the icon and connect the buttons."""
        super(FirstSetup, self).__init__(*args, **kwargs) #Setup UI as defined in First Setup UI script.
        self.setupUi(self)

        self.ImportButton.clicked.connect(self.OldNVE) #Connect buttons
        self.ImportBackButton.clicked.connect(self.BackPage)
        self.VerificationBackButton.clicked.connect(self.BackPage)
        self.ImportContinueButton.clicked.connect(self.ContinueImport)
        self.ConfirmButton.clicked.connect(self.ExitSetup)
        self.SetupNewButton.clicked.connect(self.NewNVE)
        self.account_input.setValidator(QtGui.QIntValidator())
        self.code_input.setValidator(QtGui.QIntValidator())
        self.VerificationContinueButton.clicked.connect(self.verify)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        sys.excepthook = except_hook #Replaces the standard exception handling with custom function

    def NewNVE(self):
        self.stackedWidget.setCurrentIndex(4)
        self.CreateMethod = "New"

    def OldNVE(self):
        self.stackedWidget.setCurrentIndex(4)
        self.CreateMethod = "Old"

    def verify(self):
        global EncKey
        account = self.account_input.text().strip()
        code = self.code_input.text().strip()

        codeSuccess = False

        try:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)

            sftp = paramiko.SFTPClient.from_transport(transport)

            with sftp.open(f"/VerificationCodes.txt", 'r') as remote_file:
                for line in remote_file:
                    try:
                        data = line.split(" - ")
                        if account == data[0] and code == data[1].strip():
                            codeSuccess = True
                    except:
                        pass

            sftp.close()
            transport.close()        
            
            if codeSuccess:
                EncKey = derive_key(account)
                #with open("Data/Account Verification.txt", "w") as file:
                    #file.write(f"{account} - {code}")
                writeString = f"{account} - {code}"
                save_encrypted_text(writeString, "Data/Account Verification.dat", BaseKey)
                
                if self.CreateMethod == "New":
                    self.FinishNewSetup()
                elif self.CreateMethod == "Old":
                    self.ImportNVE()
            else:
                self.errorLabel.setText("Verification failed. Please check your details and try again.")
                self.code_input.clear()

        except:
            self.errorLabel.setText("Failed to connect to Madhouse server. Please try again later.")
            self.code_input.clear()



    def FinishNewSetup(self):
        self.stackedWidget.setCurrentIndex(2)
        self.progressBar.setMinimum(0) #Create progress bar
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        #Copy graphics
        transport = paramiko.Transport((hostname, port))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)           
        
        today_str = datetime.today().strftime("%d/%m/%y")
        with open("Data/Graphics Check.txt", "w") as f:
            f.write(today_str)

        self.Counter = 0
        
        with sftp.open(f"/DateMod.txt", 'r') as remote_file:
            for line_num, line in enumerate(remote_file, start=1):
                line = line.strip()
                if not line:
                    continue
                remote_zip_path = f"/C32_{line_num}.zip"
                local_zip_path = f"C32_{line_num}.zip"
                local_bmp_path = f"Resources/Program Graphics/C32_{line_num}.bmp"

                sftp.get(remote_zip_path, local_zip_path)

                with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                    bmp_inside_zip = f"Graphics/C32_{line_num}.bmp"
                    zip_ref.extract(bmp_inside_zip, ".")
                    shutil.move(bmp_inside_zip, local_bmp_path)

                self.Counter += 1
                self.progressBar.setValue(int(98*self.Counter/128))

                try:
                    os.remove(local_zip_path)
                    os.rmdir("Graphics")
                except:
                    pass

        sftp.close()
        transport.close()
        self.ProgressLabel.setText("Setting up Data")
        with open('Data/Position Numbers.txt', 'w') as file:
            pass
        with open('Data/Last Sent.txt', 'w') as file:
            pass
        with open('Data/AutoLoad.txt', 'w') as file:
            pass
        self.TerrainKeys = {'???': '0^0^Absolute Nothingness^MPs: ???^Vis. Adj.: ???^Att. Adj.: ???^Def. Adj.: ???'}
        #with open('Data/TerrainList.txt', 'w', encoding='utf-8') as file:
            #for key, value in self.TerrainKeys.items():
                #file.write(f"{key} - {value}\n")
        lines = [f"{key} - {value}" for key, value in self.TerrainKeys.items()]
        data = "\n".join(lines)
        save_encrypted_text(data, 'Data/TerrainList.dat', EncKey)
        with open('Data/Information/Creatures.json', 'w') as file:
            pass
        with open('Data/Information/Items.json', 'w') as file:
            pass
        with open('Data/Server Turn Num.txt', 'w') as file:
            file.write(f"1")
        self.progressBar.setValue(100)
        self.stackedWidget.setCurrentIndex(3)

    def ImportNVE(self):
        """Change to the second page. Then set the icon of the folder and add an event filter so it calls LabelClick when clicked."""
        self.stackedWidget.setCurrentIndex(1)
        self.folder_icon = QtGui.QPixmap("Resources/Program Graphics/FolderIcon.png")
        self.FolderIcon.setPixmap(self.folder_icon)
        self.FolderIcon.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.event_filter = LabelClick(self.ChosenPath, self)
        self.FolderIcon.installEventFilter(self.event_filter)

    def BackPage(self):
        """Return to the first page."""
        self.stackedWidget.setCurrentIndex(0)

    def ContinueImport(self):
        """Import all required data from the old NVE.

        Check the executable exists in the chosen path, if it doesn't display an error message, otherwise continue.
        Change to page 3 and create a progress bar to show import progress.
        Check for all graphics in the old NVE and copy them across.
        Check position numbers from old NVE, add them to Position Numbers and AutoLoad in new NVE.
        Convert the old NVE Terrain List for use in the new NVE.
        Copy last order files across to new NVE.
        Convert maps in old NVE to the new format and save them to new NVE.
        Copy NVE files across to new NVE.
        Save NVE path to data.
        """
        self.NVEPath = self.ChosenPath.text().replace("\\", "/") #Windows uses backslashes for some reason, change them to forward slashes.
        if os.path.exists(self.NVEPath + "/NVE v6-3.exe"): #Check executable in chosen folder.
            self.stackedWidget.setCurrentIndex(2) #Change page
            
            self.progressBar.setMinimum(0) #Create progress bar
            self.progressBar.setMaximum(100)
            self.progressBar.setValue(0)
            
            #Copy graphics
            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)

            sftp = paramiko.SFTPClient.from_transport(transport)           
            
            today_str = datetime.today().strftime("%d/%m/%y")
            with open("Data/Graphics Check.txt", "w") as f:
                f.write(today_str)

            self.Counter = 0
            
            with sftp.open(f"/DateMod.txt", 'r') as remote_file:
                for line_num, line in enumerate(remote_file, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    remote_zip_path = f"/C32_{line_num}.zip"
                    local_zip_path = f"C32_{line_num}.zip"
                    local_bmp_path = f"Resources/Program Graphics/C32_{line_num}.bmp"

                    sftp.get(remote_zip_path, local_zip_path)

                    with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                        bmp_inside_zip = f"Graphics/C32_{line_num}.bmp"
                        zip_ref.extract(bmp_inside_zip, ".")
                        shutil.move(bmp_inside_zip, local_bmp_path)

                    self.Counter += 1
                    self.progressBar.setValue(int(43*self.Counter/128))

                    try:
                        os.remove(local_zip_path)
                        os.rmdir("Graphics")
                    except:
                        pass

            sftp.close()
            transport.close()

            
##            self.GraphicsPath = self.NVEPath + "/NVE DATA/data/DungeonWorld/Graphics/"
##            self.GraphicFilesList = os.listdir(self.GraphicsPath)
##            self.Counter = 0
##            for filename in self.GraphicFilesList:
##                self.src_file = os.path.join(self.GraphicsPath, filename)
##                self.dst_file = os.path.join("Resources/Program Graphics/", filename)
##                if os.path.isfile(self.src_file):
##                    shutil.copy(self.src_file, self.dst_file)
##                self.Counter += 1
##                self.progressBar.setValue(int(9*self.Counter/len(self.GraphicFilesList)))
                
            #Check position numbers in old NVE and update data accordingly
            self.ProgressLabel.setText("Updating Position Numbers")
            self.PosNumbers = []
            for filename in os.listdir(self.NVEPath + "/NVE DATA/data/dun/5"):
                if filename.endswith(".nve"):
                    match = re.search(r'Player(\d+)', filename)
                    if match:
                        self.PosNumbers.append(match.group(1))
            self.turnNums = []
            for i in self.PosNumbers:
                #Check to see if a new turn is available
                self.NewTurnNum = ""
                try: #Obtain value before first caret in NVE file (current turn number)
                    with open(self.NVEPath + "/NVE DATA/data/dun/5/Player" + i.strip() + ".nve", 'r') as file: #Opens the old NVE file.
                        while True:
                            self.NewTurnPosRead = file.read(1)  # Read one character at a time, appending to string
                            if not self.NewTurnPosRead or self.NewTurnPosRead == "^": #Stops at caret or EOF
                                break
                            self.NewTurnNum = self.NewTurnNum + self.NewTurnPosRead
                    self.turnNums.append(str(self.NewTurnNum))
                except:
                    self.turnNums.append(str(0))
            with open('Data/Position Numbers.txt', 'w') as file:
                for i in range(0, len(self.PosNumbers)):
                    file.write(f"{self.PosNumbers[i].strip()} - {self.turnNums[i]}\n")
            with open('Data/Last Sent.txt', 'w') as file:
                for i in self.PosNumbers:
                    file.write(f"{i.strip()} - Not sent\n")
            self.progressBar.setValue(44)
            with open('Data/AutoLoad.txt', 'w') as file:
                for i in self.PosNumbers:
                    file.write(f"{i.strip()} - \n")
            self.progressBar.setValue(45)
            
            #Take discovered terrain from old NVE and convert it into format for new NVE, adding it to the new TerrainList. I wrote this a while ago, trust it works until it doesn't.
            self.ProgressLabel.setText("Converting Terrain List")
            self.TerrainKeys = {'???': '0^0^Absolute Nothingness^MPs: ???^Vis. Adj.: ???^Att. Adj.: ???^Def. Adj.: ???'}
            if os.path.exists(self.NVEPath + "/NVE DATA/data/dun/Terrain"):
                with open(self.NVEPath + "/NVE DATA/data/dun/Terrain", 'rb') as f:
                    self.TerrainData = f.read()
                self.DataGatherStage = 0
                self.Counter=0
                self.tempID = 0
                self.tempIDA = 0
                self.tempIDB = 0
                self.tempBMPPos = 0
                self.tempBMPNum = 0
                self.tempName = ""
                self.tempMP = ""
                self.tempVis = ""
                self.tempAtt = ""
                self.tempDef = ""
                self.Found = False
                for byte in self.TerrainData:
                    if self.DataGatherStage == 0:
                        if self.Counter < 4:
                            self.tempIDA += int(byte) * (256**(self.Counter))
                            self.Counter += 1
                        elif self.Counter < 8:
                            self.tempIDB += int(byte) * (256**(self.Counter-4))
                            self.Counter += 1
                        elif self.Counter < 12:
                            self.tempBMPPos += int(byte) * (256**(self.Counter-8))
                            self.Counter += 1
                        elif self.Counter < 16:
                            self.tempBMPNum += int(byte) * (256**(self.Counter-12))
                            self.Counter += 1
                        else:
                            self.DataGatherStage = 1
                    if self.DataGatherStage == 1:
                        if chr(byte) != "Í":
                            if byte != 0:
                                self.tempName = self.tempName + chr(byte)
                        else:
                            self.DataGatherStage = 2
                    if self.DataGatherStage == 2:
                        if chr(byte) == ":":
                            self.Found = True
                        if self.Found and chr(byte) != "Í" and chr(byte) != ":" and chr(byte) != " ":
                            if byte != 0:
                                self.tempMP = self.tempMP + chr(byte)
                        elif self.Found and chr(byte) == "Í":
                            self.Found = False
                            self.DataGatherStage = 3
                    if self.DataGatherStage == 3:
                        if chr(byte) == ":":
                            self.Found = True
                        if self.Found and chr(byte) != "Í" and chr(byte) != ":" and chr(byte) != " ":
                            if byte != 0:
                                self.tempVis = self.tempVis + chr(byte)
                        elif self.Found and chr(byte) == "Í":
                            self.Found = False
                            self.DataGatherStage = 4
                    if self.DataGatherStage == 4:
                        if chr(byte) == ":":
                            self.Found = True
                        if self.Found and chr(byte) != "Í" and chr(byte) != ":" and chr(byte) != " ":
                            if byte != 0:
                                self.tempAtt = self.tempAtt + chr(byte)
                        elif self.Found and chr(byte) == "Í":
                            self.Found = False
                            self.DataGatherStage = 5
                    if self.DataGatherStage == 5:
                        if chr(byte) == ":":
                            self.Found = True
                        if self.Found and chr(byte) != "Í" and chr(byte) != ":" and chr(byte) != " ":
                            if byte != 0:
                                self.tempDef = self.tempDef + chr(byte)
                        elif self.Found and chr(byte) == "Í":
                            self.Found = False
                            self.DataGatherStage = 6
                    if self.DataGatherStage == 6:
                        if byte != 205:
                            self.DataGatherStage = 0
                            self.Counter = 1
                            if self.tempBMPNum < 200:
                                self.tempID = str(self.tempIDA) + "." + str(self.tempIDB)
                                self.TerrainKeys[self.tempID] = f"{self.tempBMPNum}^{self.tempBMPPos}^{self.tempName}^MPs: {self.tempMP}^Vis. Adj.: {self.tempVis}^Att. Adj.: {self.tempAtt}^Def. Adj.: {self.tempDef}"
                            self.tempID = 0
                            self.tempIDA = int(byte) * (256**(self.Counter-1))
                            self.tempIDB = 0
                            self.tempBMPPos = 0
                            self.tempBMPNum = 0
                            self.tempName = ""
                            self.tempMP = ""
                            self.tempVis = ""
                            self.tempAtt = ""
                            self.tempDef = ""
                        else:
                            pass
            #with open('Data/TerrainList.txt', 'w', encoding='utf-8') as file:
                #for key, value in self.TerrainKeys.items():
                    #file.write(f"{key} - {value}\n")
            lines = [f"{key} - {value}" for key, value in self.TerrainKeys.items()]
            data = "\n".join(lines)
            save_encrypted_text(data, 'Data/TerrainList.dat', EncKey)
            self.progressBar.setValue(48)

            #Convert creatures
            self.ProgressLabel.setText("Converting Creatures")
            create_summary_file(self.NVEPath + "/NVE DATA/data/dun/Masterforce Descriptions", "Data/Information/Creatures.json")
            self.progressBar.setValue(51)

            #Convert items file
            self.ProgressLabel.setText("Converting Items")
            items = parse_item_data(self.NVEPath + "/NVE DATA/data/dun/Item")
            save_items_to_file(items, "Data/Information/Items.json")
            self.progressBar.setValue(54)
            
            
            #Copy last order files
            self.ProgressLabel.setText("Copying Last Orders")
            self.LastOrdersPath = self.NVEPath + "/NVE DATA/data/dun/5/Last Orders/"
            self.LastOrdersList = os.listdir(self.LastOrdersPath)
            self.Counter = 0
            for filename in self.LastOrdersList:
                self.src_file = os.path.join(self.LastOrdersPath, filename)
                self.dst_file = os.path.join("Data/Last Orders/", filename)
                if os.path.isfile(self.src_file):
                    shutil.copy(self.src_file, self.dst_file)
                self.Counter += 1
                self.progressBar.setValue(int(54+5*self.Counter/len(self.LastOrdersList)))

            #Convert old NVE maps to new map format and save.
            self.ProgressLabel.setText("Converting Maps")
            self.MapPath = self.NVEPath + "/NVE DATA/data/dun/5/Maps/"
            with open(self.NVEPath + "/NVE DATA/data/dun/5/Maps/MapList") as f:
                self.MapList = f.readlines()
            self.Counter = 0
            for filename in self.MapList:
                try:
                    with open(os.path.join(self.MapPath, filename.strip()), 'rb') as file:
                        self.CurMapData = file.read()
                except:
                    show_warning_popup(f"No map data exists for {filename.strip()} and it will be skipped.\nIf you should have data for this map please report it as an issue.")
                    continue
                self.CurMapData = self.CurMapData.hex()
                self.CurMapData = [self.CurMapData[i:i+2] for i in range(0, len(self.CurMapData), 2)]
                self.mapWidth = int(self.CurMapData[100], 16) + int(self.CurMapData[101], 16) * 256
                self.mapHeight = int(self.CurMapData[102], 16) + int(self.CurMapData[103], 16) * 256
                self.terrainData = [self.CurMapData[i:i+24] for i in range(120, len(self.CurMapData), 24)]
                self.write_string_parts = [f"{self.mapWidth}^{self.mapHeight}"]
                for terrain in self.terrainData:
                    self.IDPart = str(int(terrain[0], 16) + int(terrain[1], 16) * 256) + "." + str(int(terrain[2], 16) + int(terrain[3], 16) * 256)
                    self.BMPNumPart = int(terrain[4], 16) + int(terrain[5], 16) * 256
                    self.BMPPosPart = int(terrain[6], 16) + int(terrain[7], 16) * 256
                    self.write_string_parts.append(f"^{self.IDPart}^{self.BMPNumPart}^{self.BMPPosPart}^0^0")
                self.write_string = ''.join(self.write_string_parts)
                #with open(os.path.join("Data/Maps/", filename.strip()), 'w') as file:
                    #file.write(self.write_string)
                save_encrypted_text(self.write_string, f'{os.path.join("Data/Maps/", filename.strip())}.dat', EncKey)
                
                self.Counter += 1
                self.progressBar.setValue(int(59+36*self.Counter/len(self.MapList)))
                
            #Copy NVE files across to new NVE
            self.ProgressLabel.setText("Copying NVE Files")
            self.NVEFilePath = self.NVEPath + "/NVE DATA/data/dun/5/Player"
            self.Counter = 0
            for i in self.PosNumbers:
                self.src_file = self.NVEFilePath + i.strip() + ".nve"
                self.dst_file = "Data/NVE Files/Player" + i.strip() + ".nve"
                shutil.copy(self.src_file, self.dst_file)
                self.Counter += 1
                self.progressBar.setValue(int(95+4*self.Counter/len(self.MapList)))
                
            with open('Data/Server Turn Num.txt', 'w') as file:
                file.write(f"1")
            self.progressBar.setValue(100)
            
            self.stackedWidget.setCurrentIndex(3) #Set page to 3     
        else:
            self.ErrorLabel.setText("Could not find NVE executable in chosen folder.") #Display error message if no executable.

    def ExitSetup(self):
        """Quit the application, and launch the main window if requested."""
##        if self.LaunchCheckBox.isChecked():
##            subprocess.Popen([sys.executable] + sys.argv)
        QtWidgets.QApplication.instance().quit()

def create_summary_file(input_directory, output_file):
    creatures_dict = {}

    for filename in os.listdir(input_directory):
        full_path = os.path.join(input_directory, filename)
        if os.path.isfile(full_path):
            name_without_ext = os.path.splitext(filename)[0].lstrip('_')

            try:
                with open(full_path, 'r', encoding='utf-8') as in_f:
                    content = in_f.read()
                
                # Escape special characters like newlines
                #escaped_content = content.encode('unicode_escape').decode('utf-8')
                
                #out_f.write(f"{name_without_ext} ^ {escaped_content}\n")
                creatures_dict[name_without_ext] = content
            except Exception as e:
                pass

    #with open(output_file, "w", encoding="utf-8") as f:
        #json.dump(creatures_dict, f, indent=4, ensure_ascii=False)
    save_encrypted_json(creatures_dict, "Data/Information/Creatures.dat", EncKey)

def read_null_terminated_string(data, offset):
    end = data.index(b'\x00', offset)
    return data[offset:end].decode('utf-8', errors='ignore'), end + 1

def parse_item_data(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    offset = 0
    num_items = struct.unpack_from("<I", data, offset)[0]
    offset += 4

    items = []

    for item_index in range(num_items):
        item = {}
        try:
            # Item name
            item['name'], offset = read_null_terminated_string(data, offset)

            # Skip padding (0xCD bytes)
            while offset < len(data) and data[offset] == 0xCD:
                offset += 1

            # 5 orders: 1 char + 3x 0xCD + 2 ints (4 bytes each)
            orders = []
            for _ in range(5):
                letter = chr(data[offset])
                offset += 1
                offset += 3  # skip 0xCDs
                number1 = struct.unpack_from('<I', data, offset)[0]
                offset += 4
                number2 = struct.unpack_from('<I', data, offset)[0]
                offset += 4
                orders.append(f"{letter} {number1} {number2}")
            item['orders'] = orders

            # Skip 7 unknown blocks of 8 bytes each
            offset += 7 * 8

            # 5 short descriptions: 2-byte len prefix + string + null
            order_descriptions = []
            for i in range(5):
                length = struct.unpack_from("<H", data, offset)[0]
                offset += 2
                if length > 1:
                    string = data[offset:offset + (length - 1)].decode('utf-8', errors='ignore')
                else:
                    string = ''
                offset += length  # always skip the whole segment (string + null terminator)
                order_descriptions.append(string)
            item['order_descriptions'] = order_descriptions

            # Read description 1
            desc1_len = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            if desc1_len > 1:
                desc1 = data[offset:offset + desc1_len - 1].decode('utf-8', errors='ignore')
            else:
                desc1 = ''
            offset += desc1_len
            item['description_1'] = desc1

            # Read description 2
            desc2_len = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            if desc2_len > 1:
                desc2 = data[offset:offset + desc2_len - 1].decode('utf-8', errors='ignore')
            else:
                desc2 = ''
            offset += desc2_len
            item['description_2'] = desc2

            items.append(item)

        except Exception as e:
            print(f"Error parsing item {item_index}: {e}")
            break

    return items

def save_items_to_file(items, filename):
    cleaned_items = {}

    for item in items:
        name = item['name']
        if name == "No Item":
            continue

        order_parts = []
        for order, desc in zip(item['orders'], item['order_descriptions']):
            if order and order[0] == '\x00':
                order = '!' + order[1:]

            order_parts.append({
                "order": order,
                "description": desc
            })

        cleaned_items[name] = {
            "description_1": item['description_1'],
            "description_2": item['description_2'],
            "orders": order_parts
        }

    cleaned_items = dict(sorted(cleaned_items.items()))

    #with open(filename, 'w', encoding='utf-8') as f:
        #json.dump(cleaned_items, f, indent=4, ensure_ascii=False)
    save_encrypted_json(cleaned_items, "Data/Information/Items.dat", EncKey)

def show_warning_popup(message):
    """Create a warning dialog, pausing execution until confirmed."""
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
    msg_box.setWindowTitle("Warning")
    msg_box.setText(message)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    msg_box.exec()

def show_update_popup():
    """Create the update dialog, pausing execution until ignored/update installed."""
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle("Update Available")
    msg_box.setText("A new version of the application is available.\nDo you want to update now?")
    msg_box.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    response = msg_box.exec()

    if response == QtWidgets.QMessageBox.StandardButton.Yes:
        updater_path = os.path.join(os.getenv('TEMP'), "updater.exe")

        response = requests.get("https://hurstnettech.github.io/NVE-Updates/updater.exe")
        with open(updater_path, 'wb') as f:
            f.write(response.content)

        install_dir = os.path.dirname(sys.argv[0])
        subprocess.Popen([updater_path, install_dir, __version__])

        sys.exit()
    else:
        pass

def show_offline_popup():
    """Create the update dialog, pausing execution until ignored/update installed."""
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle("Offline Mode")
    msg_box.setText("Failed to connect to the Madhouse server. \nThe program will now start in offline mode. \nYou will not be able to download turns or send orders while in offline mode. \nYou can view turns and fill in orders to be sent later.\nTo attempt to reconnect please restart the program.")
    msg_box.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    response = msg_box.exec()

class VerificationDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Account Verification")
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp"))
        self.setMinimumWidth(400)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel("Please enter your account number and verification code below.\nTo check your code please email: dungeonworld@madcentral.co.uk"))

        input_layout = QtWidgets.QHBoxLayout()

        account_layout = QtWidgets.QVBoxLayout()
        account_label = QtWidgets.QLabel("Account Number")
        self.account_input = QtWidgets.QLineEdit()
        self.account_input.setValidator(QtGui.QIntValidator())
        account_layout.addWidget(account_label)
        account_layout.addWidget(self.account_input)

        code_layout = QtWidgets.QVBoxLayout()
        code_label = QtWidgets.QLabel("Verification Code")
        self.code_input = QtWidgets.QLineEdit()
        self.code_input.setValidator(QtGui.QIntValidator())
        code_layout.addWidget(code_label)
        code_layout.addWidget(self.code_input)

        input_layout.addLayout(account_layout)
        input_layout.addLayout(code_layout)
        main_layout.addLayout(input_layout)

        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        main_layout.addWidget(self.error_label)        

        button_box = QtWidgets.QDialogButtonBox()
        button_box.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        main_layout.addWidget(button_box)

        button_box.accepted.connect(self.verify)
        button_box.rejected.connect(self.reject)

    def verify(self):
        account = self.account_input.text().strip()
        code = self.code_input.text().strip()

        codeSuccess = False
            
        transport = paramiko.Transport((hostname, port))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        with sftp.open(f"/VerificationCodes.txt", 'r') as remote_file:
            for line in remote_file:
                try:
                    data = line.split(" - ")
                    if account == data[0] and code == data[1].strip():
                        codeSuccess = True
                except:
                    pass

        sftp.close()
        transport.close()        
        
        if codeSuccess:
            self.accept()
        else:
            self.error_label.setText("Verification failed. Please check your details and try again.")
            self.error_label.setVisible(True)
            self.code_input.clear()

def show_verification_popup():
    """Show verification dialog and block until success or close."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    dialog = VerificationDialog()
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        #with open("Data/Account Verification.txt", "w") as file:
            #file.write(f"{dialog.account_input.text()} - {dialog.code_input.text()}")
        writeString = f"{dialog.account_input.text()} - {dialog.code_input.text()}"
        save_encrypted_text(writeString, "Data/Account Verification.dat", BaseKey)
        window.post_verify_Load()
    else:
        sys.exit()

def show_new_turn_popup(pos, selected_item):
    """Create the new turn dialog, pausing execution until ignored/downloaded."""
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle("Download new turn?")
    msg_box.setText("A new turn is available for this position.\nWould you like to download it now?")
    msg_box.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    response = msg_box.exec()

    if response == QtWidgets.QMessageBox.StandardButton.Yes:
        window.DownloadNVEButton.setEnabled(False)
        manager = window.download_pos(pos, selected_item)
        loop = QtCore.QEventLoop()
        def handler(finished_pos):
            if finished_pos == pos:
                loop.quit()
        manager.download_finished.connect(handler)
        loop.exec()
    else:
        pass


class WriteMessages(QtWidgets.QMainWindow, Ui_WriteMessages):
    """Create and handle the write messages application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(WriteMessages, self).__init__(*args, **kwargs) #Setup UI as defined in Messages UI script.
        self.setupUi(self)

        self.loaded_Pos = window.CurLoadedPos
        self.HeaderLabel.setText("Write Messages - Position " + self.loaded_Pos)
        self.messagePath = "Data/Messages/DungeonWorld5-" + self.loaded_Pos + "dun-msg"

        self.SaveButton.clicked.connect(self.SaveMessage) #Connect buttons
        self.CancelButton.clicked.connect(self.ExitMessages)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        try:
            with open(self.messagePath, 'rb') as f:
                self.strings = []
                while True:
                    length_bytes = f.read(2)
                    if not length_bytes:
                        break
                    length = int.from_bytes(length_bytes, byteorder='little')
                    string_bytes = f.read(length)
                    string_data = string_bytes[:-1].decode('ascii')
                    self.strings.append(string_data)
            self.MessageLine01.setText(self.strings[0])
            self.MessageLine02.setText(self.strings[1])
            self.MessageLine03.setText(self.strings[2])
            self.MessageLine04.setText(self.strings[3])
        except:
            pass

    def SaveMessage(self):
        """Read string values and save back to file."""
        self.strings = [self.MessageLine01.text(), self.MessageLine02.text(), self.MessageLine03.text(), self.MessageLine04.text()]
        with open(self.messagePath, 'wb') as f:
            for s in self.strings:
                string_bytes = s.encode('ascii')
                length = len(string_bytes) + 1
                length_bytes = length.to_bytes(2, byteorder='little')
                f.write(length_bytes)
                f.write(string_bytes)
                f.write(b'\x00')
        self.close()

    def ExitMessages(self):
        """Close the window."""
        self.close()

class ViewMessages(QtWidgets.QMainWindow, Ui_ViewTurn):
    """Create and handle the write messages application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(ViewMessages, self).__init__(*args, **kwargs) #Setup UI as defined in Messages UI script.
        self.setupUi(self)

        self.HeaderLabel.setText("View Messages")

        self.message_list = window.MessageList

        self.CloseButton.clicked.connect(self.ExitMessages)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.message_string = "\n".join(self.message_list)
        self.TextDisplay.setText(self.message_string)

    def ExitMessages(self):
        """Close the window."""
        self.close()

class ViewTurn(QtWidgets.QMainWindow, Ui_ViewTurn):
    """Create and handle the write messages application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(ViewTurn, self).__init__(*args, **kwargs) #Setup UI as defined in Messages UI script.
        self.setupUi(self)

        self.HeaderLabel.setText("View Turn")

        self.action_list = window.CharactersDict[window.CurLoadedChar].DataDict["Actions"]

        self.CloseButton.clicked.connect(self.ExitTurnView)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.write_string = "<br>".join(self.action_list)
        self.TextDisplay.setHtml(self.write_string)

    def ExitTurnView(self):
        """Close the window."""
        self.close()

class ViewOtherDetails(QtWidgets.QMainWindow, Ui_ViewTurn):
    """Create and handle the write messages application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(ViewOtherDetails, self).__init__(*args, **kwargs) #Setup UI as defined in Messages UI script.
        self.setupUi(self)

        self.HeaderLabel.setText("Other Details")

        self.other_details_list = window.CharactersDict[window.CurLoadedChar].DataDict["Other Details"]

        self.CloseButton.clicked.connect(self.ExitDetailsView)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.write_string = "<br>".join(self.other_details_list)
        self.TextDisplay.setHtml(self.write_string)

    def ExitDetailsView(self):
        """Close the window."""
        self.close()

class ClassOrdering(QtWidgets.QMainWindow, Ui_ClassOrdering):
    """Create and handle the class ordering application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(ClassOrdering, self).__init__(*args, **kwargs) #Setup UI as defined in Messages UI script.
        self.setupUi(self)

        self.CloseButton.clicked.connect(self.ExitOrderingView)
        self.MoveUpButton.clicked.connect(self.MoveClassUp)
        self.MoveDownButton.clicked.connect(self.MoveClassDown)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.ClassList.setStyleSheet("""
            QListWidget::item:selected {
                background-color: lightgreen;
                color: black;
            }
        """)
        font = QtGui.QFont("MS Shell Dlg 2", 10, QtGui.QFont.Weight.Bold)
        self.ClassList.setFont(font)

        self.ClassList.clear()
        for i in window.ClassOrder:
            self.ClassList.addItem(f"{i}")

    def MoveClassUp(self):
        selected_item = self.ClassList.currentItem()
        if selected_item:
            text = selected_item.text()
            idx = window.ClassOrder.index(text)
            if idx != 0:
                window.ClassOrder[idx - 1], window.ClassOrder[idx] = window.ClassOrder[idx], window.ClassOrder[idx - 1]
                self.ClassList.clear()
                for i in window.ClassOrder:
                    self.ClassList.addItem(f"{i}")

                with open('Data/Class Order.txt', 'w', encoding='utf-8') as file:
                    file.write('\n'.join(window.ClassOrder))
                self.ClassList.setCurrentRow(idx-1)

    def MoveClassDown(self):
        selected_item = self.ClassList.currentItem()
        if selected_item:
            text = selected_item.text()
            idx = window.ClassOrder.index(text)
            if idx != len(window.ClassOrder) - 1:
                window.ClassOrder[idx], window.ClassOrder[idx + 1] = window.ClassOrder[idx + 1], window.ClassOrder[idx]
                self.ClassList.clear()
                for i in window.ClassOrder:
                    self.ClassList.addItem(f"{i}")

                with open('Data/Class Order.txt', 'w', encoding='utf-8') as file:
                    file.write('\n'.join(window.ClassOrder))
                self.ClassList.setCurrentRow(idx+1)

    def ExitOrderingView(self):
        """Close the window."""
        self.close()

class Settings(QtWidgets.QMainWindow, Ui_Settings):
    """Create and handle the settings application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(Settings, self).__init__(*args, **kwargs) #Setup UI as defined in Settings UI script.
        self.setupUi(self)

        self.SaveButton.clicked.connect(self.SaveSettings)
        self.CancelButton.clicked.connect(self.ExitSettings)
        self.OrderButton.clicked.connect(self.OpenOrdering)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.subheadings = [self.AppearanceLabel, self.CharacterNavigationLabel, self.WarningLevelsLabel]
        self.standard_labels = [self.ThemeLabel, self.ScalingLabel, self.OrderLabel, self.ThemeLabel_6, self.ThemeLabel_7, self.HealthLabel, self.LastAteLabel, self.LastSleptLabel, self.AccountLabel]
        self.descriptions = [self.ScalingNote]

        self.subheading_font = QtGui.QFont()
        self.subheading_font.setPointSize(12)
        self.subheading_font.setBold(True)
        self.standard_font = QtGui.QFont()
        self.standard_font.setPointSize(10)
        self.description_font = QtGui.QFont()
        self.description_font.setPointSize(8)

        for label in self.subheadings:
            label.setFont(self.subheading_font)
        for label in self.standard_labels:
            label.setFont(self.standard_font)
        for label in self.descriptions:
            label.setFont(self.description_font)

        if "Custom" in SettingsDict["scaling"]:
            self.CustomScaling.setText(SettingsDict["scaling"].split()[1])
            SettingsDict["scaling"] = "Custom"
            self.CustomScaling.setEnabled(True)
        else:
            self.CustomScaling.setEnabled(False)

        if SettingsDict["Use Custom Class Ordering"] == "True":
            self.OrderCheck.setChecked(True)
        else:
            self.OrderCheck.setChecked(False)

        self.CustomScaling.setValidator(window.validator_numbers)

        self.ThemeBox.addItems(["Classic (Old NVE)", "Papyrus", "Windows Default"]) #, "Slate"
        self.ThemeBox.setCurrentText(SettingsDict["theme"])
        self.ScalingBox.addItems(["25%", "50%", "75%", "100% (Recommended)", "125%", "150%", "175%", "200%", "Custom"])
        self.ScalingBox.setCurrentText(SettingsDict["scaling"])
        self.HealthAmber.setText(SettingsDict["Amber Health"])
        self.HealthRed.setText(SettingsDict["Red Health"])
        self.AteAmber.setText(SettingsDict["Amber Ate"])
        self.AteRed.setText(SettingsDict["Red Ate"])
        self.SleptAmber.setText(SettingsDict["Amber Slept"])
        self.SleptRed.setText(SettingsDict["Red Slept"])
        self.AccountAmber.setText(SettingsDict["Amber Account"])
        self.AccountRed.setText(SettingsDict["Red Account"])

        self.HealthAmber.setValidator(window.validator_numbers)
        self.HealthRed.setValidator(window.validator_numbers)
        self.AteAmber.setValidator(window.validator_numbers)
        self.AteRed.setValidator(window.validator_numbers)
        self.SleptAmber.setValidator(window.validator_numbers)
        self.SleptRed.setValidator(window.validator_numbers)
        self.AccountAmber.setValidator(window.validator_numbers)
        self.AccountRed.setValidator(window.validator_numbers)

        self.ScalingBox.activated.connect(self.checkCustom)

    def checkCustom(self):
        if "Custom" in self.ScalingBox.currentText():
            self.CustomScaling.setEnabled(True)
        else:
            self.CustomScaling.setEnabled(False)

    def OpenOrdering(self):
        if hasattr(self, 'orderingWindow') and self.orderingWindow is not None:
            if self.orderingWindow.isVisible():
                self.orderingWindow.raise_()
                self.orderingWindow.activateWindow()
                return
            else:
                self.orderingWindow.deleteLater()
                self.orderingWindow = None
        self.orderingWindow = ClassOrdering() 
        self.orderingWindow.show()
        self.orderingWindow.setWindowTitle("Order classes")

    def SaveSettings(self):
        SettingsDict["theme"] = self.ThemeBox.currentText()
        checkRestart = SettingsDict["scaling"]
        if "Custom" in self.ScalingBox.currentText() and self.CustomScaling.text() != '':
            SettingsDict["scaling"] = f"{self.ScalingBox.currentText()} {self.CustomScaling.text()}"
        elif "Custom" not in self.ScalingBox.currentText():
            SettingsDict["scaling"] = self.ScalingBox.currentText()
        if checkRestart != SettingsDict["scaling"]:
            checkRestart = True
        else:
            checkRestart = False
        if self.OrderCheck.isChecked():
            SettingsDict["Use Custom Class Ordering"] = "True"
        else:
            SettingsDict["Use Custom Class Ordering"] = "False"
        if self.HealthAmber.text() != '':
            SettingsDict["Amber Health"] = self.HealthAmber.text()
        else:
            SettingsDict["Amber Health"] = "25"
        if self.HealthRed.text() != '':
            SettingsDict["Red Health"] = self.HealthRed.text()
        else:
            SettingsDict["Red Health"] = "0"
        if self.AteAmber.text() != '':
            SettingsDict["Amber Ate"] = self.AteAmber.text()
        else:
            SettingsDict["Amber Ate"] = "5"
        if self.AteRed.text() != '':
            SettingsDict["Red Ate"] = self.AteRed.text()
        else:
            SettingsDict["Red Ate"] = "10"
        if self.SleptAmber.text() != '':
            SettingsDict["Amber Slept"] = self.SleptAmber.text()
        else:
            SettingsDict["Amber Slept"] = "5"
        if self.SleptRed.text() != '':
            SettingsDict["Red Slept"] = self.SleptRed.text()
        else:
            SettingsDict["Red Slept"] = "10"
        if self.AccountAmber.text() != '':
            SettingsDict["Amber Account"] = self.AccountAmber.text()
        else:
            SettingsDict["Amber Account"] = "10"
        if self.AccountRed.text() != '':
            SettingsDict["Red Account"] = self.AccountRed.text()
        else:
            SettingsDict["Red Account"] = "0"
        with open('settings.txt', 'w') as file:
            for key, value in SettingsDict.items():
                file.write(f"{key}: {value}\n")
        if SettingsDict["theme"] == "Classic (Old NVE)": #Set background image and text colour
            window.update_styleSheet("Resources/Program Graphics/backdrop.bmp", "#DEE3DE", "#CBD0CC")
        elif SettingsDict["theme"] == "Papyrus":
            window.update_styleSheet("Resources/Program Graphics/papyrus.jpg", "#592824", "#CBD0CC")
        elif SettingsDict["theme"] == "Windows Default":
            window.update_styleSheet("Default", "#1A1A1A", "#CBD0CC")
        elif SettingsDict["theme"] == "Slate":
            window.update_styleSheet("Resources/Program Graphics/stone.jpg", "#fbf7f5", "#CBD0CC")
        if SettingsDict["Use Custom Class Ordering"] == "True" and window.PositionLoaded:
            tempcharList = window.CharactersList.copy()
            window.CharactersList = []
            for ClassName in window.ClassOrder:
                for CharNum in tempcharList:
                    if window.CharactersDict[CharNum].DataDict["Class"] == ClassName:
                        window.CharactersList.append(CharNum)
            window.LoadCharacter(window.CharactersList[window.CurCharIndex-1])
        if checkRestart:
            #prompt_restart()
            pass
        self.close()

    def ExitSettings(self):
        """Close the window."""
        self.close()

def prompt_restart():
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle("Restart Required")
    msg_box.setText("Some changes require a restart to take effect.\nWould you like to restart now?")
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)

    result = msg_box.exec()

    if result == QtWidgets.QMessageBox.StandardButton.Yes:
        restart_program()

def restart_program():
    env = os.environ.copy()
    if getattr(sys, 'frozen', False):
        meipass = sys._MEIPASS
        plugin_path = os.path.join(meipass, 'PyQt6', 'Qt6', 'plugins')
        env['QT_PLUGIN_PATH'] = plugin_path

        executable = sys.executable
    else:
        executable = sys.executable

    subprocess.Popen([executable] + sys.argv[1:], env=env)
    QtWidgets.QApplication.quit()

class ItemLibrary(QtWidgets.QMainWindow, Ui_ItemLibrary):
    """Create and handle the item library application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(ItemLibrary, self).__init__(*args, **kwargs) #Setup UI as defined in ItemLibrary UI script.
        self.setupUi(self)

        self.CloseButton.clicked.connect(self.ExitLibrary)
        self.LastItemButton.clicked.connect(self.select_previous_item)
        self.NextItemButton.clicked.connect(self.select_next_item)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.LtrEdits = [self.Ltr_Edit1, self.Ltr_Edit2, self.Ltr_Edit3, self.Ltr_Edit4, self.Ltr_Edit5]
        self.Code1Edits = [self.Code1_Edit1, self.Code1_Edit2, self.Code1_Edit3, self.Code1_Edit4, self.Code1_Edit5]
        self.Code2Edits = [self.Code2_Edit1, self.Code2_Edit2, self.Code2_Edit3, self.Code2_Edit4, self.Code2_Edit5]
        self.DescriptionEdits = [self.Description_Edit1, self.Description_Edit2, self.Description_Edit3, self.Description_Edit4, self.Description_Edit5]
        self.WriteButtons = [self.WriteOrderButton1, self.WriteOrderButton2, self.WriteOrderButton3, self.WriteOrderButton4, self.WriteOrderButton5]

        self.regex_letters = QtCore.QRegularExpression("[a-zA-Z]")
        self.validator_letters = QtGui.QRegularExpressionValidator(self.regex_letters, self)
        
        self.regex_numbers = QtCore.QRegularExpression("[0-9]+")
        self.validator_numbers = QtGui.QRegularExpressionValidator(self.regex_numbers, self)

        self.all_item_names = list(window.saved_item_data.keys())
        self.ItemsListBox.addItems(self.all_item_names)

        self.ItemSearchEntry.textChanged.connect(self.filter_search_results)
        self.ItemsListBox.currentTextChanged.connect(self.update_item_description)
        self.PlayerNotes.textChanged.connect(self.update_player_notes)

        for i in range(0, 5):
            self.LtrEdits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))
            self.LtrEdits[i].setValidator(self.validator_letters)
            self.Code1Edits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))
            self.Code2Edits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))
            self.Code1Edits[i].setValidator(self.validator_numbers)
            self.Code2Edits[i].setValidator(self.validator_numbers)
            self.DescriptionEdits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))

            self.WriteButtons[i].clicked.connect(lambda _, idx=i: self.write_order(idx))

        if self.all_item_names:
            self.update_item_description(self.all_item_names[0])

    def filter_search_results(self, text):
        text = text.lower()

        self.ItemsListBox.clear()
        matches = [name for name in self.all_item_names if text in name.lower()]
        self.ItemsListBox.addItems(matches)

    def update_player_notes(self):
        current_item = self.ItemsListBox.currentText()
        if current_item in window.saved_item_data:
            note = self.PlayerNotes.toPlainText()
            item_data = window.saved_item_data[current_item]

            # Ensure there's a slot for the second description
            #while len(item_data) < 2:
                #item_data.append("")

            item_data["description_2"] = note

    def update_order(self, index):
        current_item = self.ItemsListBox.currentText()
        if current_item not in window.saved_item_data:
            return

        if self.LtrEdits[index].text().strip().islower():
            self.LtrEdits[index].blockSignals(True)
            self.LtrEdits[index].setText(self.LtrEdits[index].text().strip().upper())
            self.LtrEdits[index].blockSignals(False)

        letter = self.LtrEdits[index].text().strip() or '!'
        code1_text = self.Code1Edits[index].text().strip()
        code2_text = self.Code2Edits[index].text().strip()
        description = self.DescriptionEdits[index].text().strip()

        try:
            code1 = int(code1_text) if code1_text else 0
        except ValueError:
            code1 = 0

        try:
            code2 = int(code2_text) if code2_text else 0
        except ValueError:
            code2 = 0

        parts = [letter]
        parts.append(str(code1))
        parts.append(str(code2))
        if description:
            parts.append(description)

        new_order_string = " ".join(parts)

        window.saved_item_data[current_item]["orders"][index]["order"] = new_order_string

    def write_order(self, index):
        try:
            self.focused_Order = int(window.OrderEditsList.index(window.focus_tracker.last_focused_widget)/3)
        except:
            self.focused_Order = 0
        self.writeLetterIndex = self.focused_Order * 3
        if window.OrderEditsList[self.writeLetterIndex].isEnabled():
            window.OrderEditsList[self.writeLetterIndex].blockSignals(True)
            window.OrderEditsList[self.writeLetterIndex].setText(self.LtrEdits[index].text().strip())
            window.OrderEditsList[self.writeLetterIndex].blockSignals(False)
            window.OrderEditsList[self.writeLetterIndex+1].blockSignals(True)
            window.OrderEditsList[self.writeLetterIndex+1].setText(self.Code1Edits[index].text().strip())
            window.OrderEditsList[self.writeLetterIndex+1].blockSignals(False)
            window.OrderEditsList[self.writeLetterIndex+2].blockSignals(True)
            window.OrderEditsList[self.writeLetterIndex+2].setText(self.Code2Edits[index].text().strip())
            window.OrderEditsList[self.writeLetterIndex+2].blockSignals(False)
            if self.writeLetterIndex < 42 and window.OrderEditsList[self.writeLetterIndex+3].isEnabled():
                window.OrderEditsList[self.writeLetterIndex+3].setFocus()
                window.focus_tracker.last_focused_widget = window.OrderEditsList[self.writeLetterIndex+3]
                window.OrderEditsList[self.writeLetterIndex].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+1].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+2].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+3].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+4].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+5].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            window.render_movement()

    def update_item_description(self, item_name):
        description = window.saved_item_data[item_name]["description_1"]
        self.ItemDescription.setPlainText(description)

        notes = window.saved_item_data[item_name]["description_2"]
        self.PlayerNotes.blockSignals(True)
        self.PlayerNotes.setPlainText(notes)
        self.PlayerNotes.blockSignals(False)

        for i in range(0,5):
            order_str = window.saved_item_data[item_name]["orders"][i]["order"] + " " + window.saved_item_data[item_name]["orders"][i]["description"]
            parts = order_str.split(maxsplit=3)
            while len(parts) < 4:
                parts.append("")
            letter, num1, num2, desc = parts
            letter = "" if letter == "!" else letter.upper()
            num1 = "" if num1 == "0" else num1
            num2 = "" if num2 == "0" else num2
            desc = desc.strip()

            self.LtrEdits[i].blockSignals(True)
            self.Code1Edits[i].blockSignals(True)
            self.Code2Edits[i].blockSignals(True)
            self.DescriptionEdits[i].blockSignals(True)
            self.LtrEdits[i].setText(letter)
            self.Code1Edits[i].setText(num1)
            self.Code2Edits[i].setText(num2)
            self.DescriptionEdits[i].setText(desc)
            self.LtrEdits[i].blockSignals(False)
            self.Code1Edits[i].blockSignals(False)
            self.Code2Edits[i].blockSignals(False)
            self.DescriptionEdits[i].blockSignals(False)

    def select_previous_item(self):
        count = self.ItemsListBox.count()
        if count == 0:
            return  # No items to select

        current_index = self.ItemsListBox.currentIndex()
        new_index = (current_index - 1) % count
        self.ItemsListBox.setCurrentIndex(new_index)

    def select_next_item(self):
        count = self.ItemsListBox.count()
        if count == 0:
            return  # No items to select

        current_index = self.ItemsListBox.currentIndex()
        new_index = (current_index + 1) % count
        self.ItemsListBox.setCurrentIndex(new_index)

    def ExitLibrary(self):
        """Close the window."""
        #with open("Data/Information/Items.json", 'w', encoding='utf-8') as file:
            #json.dump(window.saved_item_data, file, indent=4, ensure_ascii=False)
        save_encrypted_json(window.saved_item_data, "Data/Information/Items.dat", EncKey)
        self.close()

class SkillLibrary(QtWidgets.QMainWindow, Ui_SkillsLibrary):
    """Create and handle the skill library application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(SkillLibrary, self).__init__(*args, **kwargs) #Setup UI as defined in SkillLibrary UI script.
        self.setupUi(self)

        self.CloseButton.clicked.connect(self.ExitLibrary)
        self.LastItemButton.clicked.connect(self.select_previous_skill)
        self.NextItemButton.clicked.connect(self.select_next_skill)
        self.AddSkillButton.clicked.connect(self.create_new_skill)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.LtrEdits = [self.Ltr_Edit1, self.Ltr_Edit2, self.Ltr_Edit3, self.Ltr_Edit4, self.Ltr_Edit5]
        self.Code1Edits = [self.Code1_Edit1, self.Code1_Edit2, self.Code1_Edit3, self.Code1_Edit4, self.Code1_Edit5]
        self.Code2Edits = [self.Code2_Edit1, self.Code2_Edit2, self.Code2_Edit3, self.Code2_Edit4, self.Code2_Edit5]
        self.DescriptionEdits = [self.Description_Edit1, self.Description_Edit2, self.Description_Edit3, self.Description_Edit4, self.Description_Edit5]
        self.WriteButtons = [self.WriteOrderButton1, self.WriteOrderButton2, self.WriteOrderButton3, self.WriteOrderButton4, self.WriteOrderButton5]

        self.regex_letters = QtCore.QRegularExpression("[a-zA-Z]")
        self.validator_letters = QtGui.QRegularExpressionValidator(self.regex_letters, self)
        
        self.regex_numbers = QtCore.QRegularExpression("[0-9]+")
        self.validator_numbers = QtGui.QRegularExpressionValidator(self.regex_numbers, self)

        self.all_skill_names = list(window.saved_skill_data.keys())
        self.SkillsListBox.addItems(self.all_skill_names)

        self.SkillSearchEntry.textChanged.connect(self.filter_search_results)
        self.SkillsListBox.currentTextChanged.connect(self.update_skill_description)
        self.SkillDescription.textChanged.connect(self.update_description)

        self.XPToLearnEntry.textChanged.connect(self.update_XPLearn)
        self.FailedXPEntry.textChanged.connect(self.update_XPFailed)
        self.GPtoLearnEntry.textChanged.connect(self.update_GPLearn)
        self.FailedGPEntry.textChanged.connect(self.update_GPFailed)
        self.TeacherEntry.textChanged.connect(self.update_Teacher)
        self.PreRequisitesEntry.textChanged.connect(self.update_PreReq)
        self.ChanceEntry.textChanged.connect(self.update_Chance)

        for i in range(0, 5):
            self.LtrEdits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))
            self.LtrEdits[i].setValidator(self.validator_letters)
            self.Code1Edits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))
            self.Code2Edits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))
            self.Code1Edits[i].setValidator(self.validator_numbers)
            self.Code2Edits[i].setValidator(self.validator_numbers)
            self.DescriptionEdits[i].textChanged.connect(lambda _, idx=i: self.update_order(idx))

            self.WriteButtons[i].clicked.connect(lambda _, idx=i: self.write_order(idx))

        if self.all_skill_names:
            self.update_skill_description(self.all_skill_names[0])

    def create_new_skill(self):
        text = self.SkillSearchEntry.text()
        if text not in window.saved_skill_data:
            window.saved_skill_data[text] = ['', '', '', '', '', '', '', '', '! 0 0', '! 0 0', '! 0 0', '! 0 0', '! 0 0']
            self.all_skill_names = list(window.saved_skill_data.keys())
            self.filter_search_results(text)
            index = self.SkillsListBox.findText(text)
            if index != -1:
                self.SkillsListBox.setCurrentIndex(index)

    def filter_search_results(self, text):
        text = text.lower()
        
        matches = [name for name in self.all_skill_names if text in name.lower()]
        self.SkillsListBox.clear()
        self.SkillsListBox.addItems(matches)

    def update_description(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            descript = self.SkillDescription.toPlainText()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[0] = descript

    def update_XPLearn(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.XPToLearnEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[1] = new_data

    def update_XPFailed(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.FailedXPEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[2] = new_data

    def update_GPLearn(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.GPtoLearnEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[3] = new_data

    def update_GPFailed(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.FailedGPEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[4] = new_data

    def update_Teacher(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.TeacherEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[5] = new_data

    def update_PreReq(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.PreRequisitesEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[6] = new_data

    def update_Chance(self):
        current_skill = self.SkillsListBox.currentText()
        if current_skill in window.saved_skill_data:
            new_data = self.ChanceEntry.text()
            skill_data = window.saved_skill_data[current_skill]
            skill_data[7] = new_data

    def update_order(self, index):
        current_skill = self.SkillsListBox.currentText()
        if current_skill not in window.saved_skill_data:
            return

        if self.LtrEdits[index].text().strip().islower():
            self.LtrEdits[index].blockSignals(True)
            self.LtrEdits[index].setText(self.LtrEdits[index].text().strip().upper())
            self.LtrEdits[index].blockSignals(False)

        letter = self.LtrEdits[index].text().strip() or '!'
        code1_text = self.Code1Edits[index].text().strip()
        code2_text = self.Code2Edits[index].text().strip()
        description = self.DescriptionEdits[index].text().strip()

        try:
            code1 = int(code1_text) if code1_text else 0
        except ValueError:
            code1 = 0

        try:
            code2 = int(code2_text) if code2_text else 0
        except ValueError:
            code2 = 0

        parts = [letter]
        parts.append(str(code1))
        parts.append(str(code2))
        if description:
            parts.append(description)

        new_order_string = " ".join(parts)

        window.saved_skill_data[current_skill][index + 8] = new_order_string

    def write_order(self, index):
        try:
            self.focused_Order = int(window.OrderEditsList.index(window.focus_tracker.last_focused_widget)/3)
        except:
            self.focused_Order = 0
        self.writeLetterIndex = self.focused_Order * 3
        if window.OrderEditsList[self.writeLetterIndex].isEnabled():
            window.OrderEditsList[self.writeLetterIndex].blockSignals(True)
            window.OrderEditsList[self.writeLetterIndex].setText(self.LtrEdits[index].text().strip())
            window.OrderEditsList[self.writeLetterIndex].blockSignals(False)
            window.OrderEditsList[self.writeLetterIndex+1].blockSignals(True)
            window.OrderEditsList[self.writeLetterIndex+1].setText(self.Code1Edits[index].text().strip())
            window.OrderEditsList[self.writeLetterIndex+1].blockSignals(False)
            window.OrderEditsList[self.writeLetterIndex+2].blockSignals(True)
            window.OrderEditsList[self.writeLetterIndex+2].setText(self.Code2Edits[index].text().strip())
            window.OrderEditsList[self.writeLetterIndex+2].blockSignals(False)
            if self.writeLetterIndex < 42 and window.OrderEditsList[self.writeLetterIndex+3].isEnabled():
                window.OrderEditsList[self.writeLetterIndex+3].setFocus()
                window.focus_tracker.last_focused_widget = window.OrderEditsList[self.writeLetterIndex+3]
                window.OrderEditsList[self.writeLetterIndex].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+1].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+2].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+3].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+4].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+5].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            window.render_movement()

    def update_skill_description(self, skill_name):
        description = window.saved_skill_data.get(skill_name, [''])[0]
        self.SkillDescription.blockSignals(True)
        self.SkillDescription.setPlainText(description)
        self.SkillDescription.blockSignals(False)

        XPLearn = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[1]
        self.XPToLearnEntry.blockSignals(True)
        self.XPToLearnEntry.setText(XPLearn)
        self.XPToLearnEntry.blockSignals(False)

        XPFail = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[2]
        self.FailedXPEntry.blockSignals(True)
        self.FailedXPEntry.setText(XPFail)
        self.FailedXPEntry.blockSignals(False)

        GPLearn = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[3]
        self.GPtoLearnEntry.blockSignals(True)
        self.GPtoLearnEntry.setText(GPLearn)
        self.GPtoLearnEntry.blockSignals(False)

        GPFail = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[4]
        self.FailedGPEntry.blockSignals(True)
        self.FailedGPEntry.setText(GPFail)
        self.FailedGPEntry.blockSignals(False)

        Teacher = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[5]
        self.TeacherEntry.blockSignals(True)
        self.TeacherEntry.setText(Teacher)
        self.TeacherEntry.blockSignals(False)

        PreReq = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[6]
        self.PreRequisitesEntry.blockSignals(True)
        self.PreRequisitesEntry.setText(PreReq)
        self.PreRequisitesEntry.blockSignals(False)

        Chance = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[7]
        self.ChanceEntry.blockSignals(True)
        self.ChanceEntry.setText(Chance)
        self.ChanceEntry.blockSignals(False)

        for i in range(0,5):
            order_str = window.saved_skill_data.get(skill_name, ['', '', '', '', '', '', '', '', '', '', '', '', ''])[8+i]
            parts = order_str.split(maxsplit=3)
            while len(parts) < 4:
                parts.append("")
            letter, num1, num2, desc = parts
            letter = "" if letter == "!" else letter.upper()
            num1 = "" if num1 == "0" else num1
            num2 = "" if num2 == "0" else num2
            desc = desc.strip()

            self.LtrEdits[i].blockSignals(True)
            self.Code1Edits[i].blockSignals(True)
            self.Code2Edits[i].blockSignals(True)
            self.DescriptionEdits[i].blockSignals(True)
            self.LtrEdits[i].setText(letter)
            self.Code1Edits[i].setText(num1)
            self.Code2Edits[i].setText(num2)
            self.DescriptionEdits[i].setText(desc)
            self.LtrEdits[i].blockSignals(False)
            self.Code1Edits[i].blockSignals(False)
            self.Code2Edits[i].blockSignals(False)
            self.DescriptionEdits[i].blockSignals(False)

            

    def select_previous_skill(self):
        count = self.SkillsListBox.count()
        if count == 0:
            return  # No items to select

        current_index = self.SkillsListBox.currentIndex()
        new_index = (current_index - 1) % count
        self.SkillsListBox.setCurrentIndex(new_index)

    def select_next_skill(self):
        count = self.SkillsListBox.count()
        if count == 0:
            return  # No items to select

        current_index = self.SkillsListBox.currentIndex()
        new_index = (current_index + 1) % count
        self.SkillsListBox.setCurrentIndex(new_index)

    def ExitLibrary(self):
        """Close the window."""
        window.saved_skill_data = dict(sorted(window.saved_skill_data.items()))
        #with open("Data/Information/Skills.json", "w", encoding="utf-8") as f:
            #json.dump(window.saved_skill_data, f, ensure_ascii=False, indent=2)
        save_encrypted_json(window.saved_skill_data, "Data/Information/Skills.dat", EncKey)
        
        self.close()

class CreatureLibrary(QtWidgets.QMainWindow, Ui_Creatures):
    """Create and handle the creature library application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(CreatureLibrary, self).__init__(*args, **kwargs) #Setup UI as defined in CreatureLibrary UI script.
        self.setupUi(self)

        self.CloseButton.clicked.connect(self.ExitLibrary)
        self.LastCreatureButton.clicked.connect(self.select_previous_creature)
        self.NextCreatureButton.clicked.connect(self.select_next_creature)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        self.all_creature_names = list(window.saved_creature_data.keys())
        self.CreaturesListBox.addItems(self.all_creature_names)

        self.CreatureSearchEntry.textChanged.connect(self.filter_search_results)
        self.CreaturesListBox.currentTextChanged.connect(self.update_creature_description)

        if self.all_creature_names:
            self.update_creature_description(self.all_creature_names[0])

    def filter_search_results(self, text):
        text = text.lower()

        matches = [name for name in self.all_creature_names if text in name.lower()]
        self.CreaturesListBox.clear()
        self.CreaturesListBox.addItems(matches)

    def update_creature_description(self, creature_name):
        if creature_name in window.saved_creature_data:
            escaped_text = window.saved_creature_data[creature_name]
            decoded_text = bytes(escaped_text, "utf-8").decode("unicode_escape")
            self.CreatureDescription.setPlainText(decoded_text)
        else:
            self.CreatureDescription.setPlainText("")

    def select_previous_creature(self):
        count = self.CreaturesListBox.count()
        if count == 0:
            return  # No items to select

        current_index = self.CreaturesListBox.currentIndex()
        new_index = (current_index - 1) % count
        self.CreaturesListBox.setCurrentIndex(new_index)

    def select_next_creature(self):
        count = self.CreaturesListBox.count()
        if count == 0:
            return  # No items to select

        current_index = self.CreaturesListBox.currentIndex()
        new_index = (current_index + 1) % count
        self.CreaturesListBox.setCurrentIndex(new_index)

    def ExitLibrary(self):
        """Close the window."""
        self.close()

class ProgressPopup(QtWidgets.QMainWindow, Ui_ProgressWindow):
    """Create and handle the write messages application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        super(ProgressPopup, self).__init__(*args, **kwargs) #Setup UI as defined in Progress UI script.
        self.setupUi(self)

        self.position = window.CurLoadedPos
        self.setWindowTitle(f"Loading Position {self.position}")
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon
        self.ProgressLabel.setText("Starting loading thread")
        
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

    def update_progress(self, value):
        self.progressBar.setValue(value)
        #if value >= 100:
            #self.close()

    def update_label(self, text):
        self.ProgressLabel.setText(text)

class PositionLoader(QtCore.QObject):
    progress_updated = QtCore.pyqtSignal(int)
    label_updated = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, PosNumber, window):
        super().__init__()
        self.PosNumber = PosNumber
        self.window = window

    def run(self):
        self.label_updated.emit(f"Loading position {self.PosNumber} data")

        #Read in position data
        with open('Data/NVE Files/Player'+self.window.CurLoadedPos+'.nve', 'r') as f: #Reads in all data from the nve file and splits it by the carats, will need to take this out of memory once processed as it can be quite big.
            self.window.PosData = f.read().split('^')

        try:
            self.label_updated.emit(f"Reading message data")
            self.progress_updated.emit(3)
        except:
            pass
              
        self.window.CurLoadedMap = ""
        self.window.GameNum = self.window.PosData[1]
        self.window.AccountNum = self.window.PosData[4]
        self.window.DueDate = self.window.PosData[6].replace("Turn Due ", "", 1) #Record due date/account balance
        self.window.Balance = self.window.PosData[7].replace("Account Balance ", "", 1)
        
        self.window.Balance = re.sub(r'\.-', '.', self.window.Balance) #Fix Steve's nonsensical formatting

        self.window.OrderDueDateLabel.setText(f"Turn Due: {self.window.DueDate}")
        self.window.AccountBalanceLabel.setText(f"{self.window.Balance}")
        if float(self.window.Balance[1:]) <= int(SettingsDict["Red Account"]):
            self.window.AccountBalanceLabel.setStyleSheet("color: #D40000;")
        elif float(self.window.Balance[1:]) <= int(SettingsDict["Amber Account"]):
            self.window.AccountBalanceLabel.setStyleSheet("color: #FFBF00;")
        else:
            self.window.AccountBalanceLabel.setStyleSheet("")

        self.window.MessageList = [] #Next deal with messages
        self.window.index = 8
        while self.window.PosData[self.window.index] != "|":
            if self.window.PosData[self.window.index].strip() != "":
                self.window.MessageList.append(self.window.PosData[self.window.index])
            else:
                self.window.MessageList.append("")
            self.window.index += 1
        self.window.index += 1

        #Now going through characters, using a while loop now so we have more manual control over indexes.
        self.window.CharactersDict = {}
        self.window.CharactersList = [] #Stores keys for use in dict
        self.window.MapsDict = {}
        self.window.NewTerrainDict = {}
        self.window.CharCount = self.window.PosData.count("±")

        self.window.count=0
        self.window.localItems = {}

        while True:
            self.window.CurCharNum = self.window.PosData[self.window.index+4] #We make our way through all of each characters data, saving it to an instance of the class as is relevant
            try:
                self.label_updated.emit(f"Reading character {self.window.CurCharNum} data")
                self.progress_updated.emit(int(5+90*self.window.count/self.window.CharCount))
            except:
                pass
            self.window.CharactersDict[self.window.CurCharNum] = Character()
            self.window.CharactersDict[self.window.CurCharNum].add_data("Class", self.window.PosData[self.window.index+2])
            if self.window.PosData[self.window.index+2] not in window.ClassOrder:
                window.ClassOrder.append(self.window.PosData[self.window.index+2])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Name", self.window.PosData[self.window.index+3])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Number", self.window.CurCharNum)
            self.window.CharactersList.append(self.window.CurCharNum)
            self.window.CharactersDict[self.window.CurCharNum].add_data("NumOrders", self.window.PosData[self.window.index+5])
            self.window.CharactersDict[self.window.CurCharNum].add_data("CharCost", self.window.PosData[self.window.index+6])
            self.window.CharactersDict[self.window.CurCharNum].add_data("CharCredits", self.window.PosData[self.window.index+7])
            self.window.CharactersDict[self.window.CurCharNum].add_data("MapName", self.window.PosData[self.window.index+9])
            self.window.CurMapName = self.window.PosData[self.window.index+9]
            self.window.CharactersDict[self.window.CurCharNum].add_data("MapDisplayName", self.window.PosData[self.window.index+10])
            try: #Load map from file if new, otherwise flag new map needed if it doesn't exist.
                self.window.NewMap = False
                if self.window.CurMapName not in self.window.MapsDict:       
                    #with open(f'Data/Maps/{self.window.CurMapName}', 'r') as file:
                        #self.window.MapsDict[self.window.CurMapName] = GameMap()
                        #self.window.MapsDict[self.window.CurMapName].DataList = file.read().split("^")
                    self.window.MapsDict[self.window.CurMapName] = GameMap()
                    self.window.MapsDict[self.window.CurMapName].DataList = load_encrypted_text(f'Data/Maps/{self.window.CurMapName}', f'Data/Maps/{self.window.CurMapName}.dat', EncKey).split("^")
                    
            except:
                self.window.NewMap = True
            self.window.CharactersDict[self.window.CurCharNum].add_data("TerrainName", self.window.PosData[self.window.index+10])
            self.window.CharactersDict[self.window.CurCharNum].add_data("CharGraphic", [self.window.PosData[self.window.index+13], self.window.PosData[self.window.index+12]]) #Number of bitmap, then position within bitmap
            if self.window.PosData[self.window.index+6].split()[0] == "Shop":
                self.window.ShopTest = True
            else:
                self.window.ShopTest = False
            if self.window.ShopTest:
                self.window.index = self.window.index+14
                self.window.EnhancementActiveList = []
                while self.window.PosData[self.window.index] != "Shop Stores":
                    self.window.EnhancementActiveList.append(self.window.PosData[self.window.index])
                    self.window.index += 1
                self.window.CharactersDict[self.window.CurCharNum].add_data("EnhancementsAndActives", self.window.EnhancementActiveList)
            else:
                self.window.index=self.window.index+16
                self.window.EquipmentNames = []
                for i in self.window.SlotList:
                    self.window.EquipmentNames.append(self.window.PosData[self.window.index-1])
                    if self.window.PosData[self.window.index] == "1":
                        if self.window.PosData[self.window.index+5] == "1":
                            self.window.CharactersDict[self.window.CurCharNum].add_data(i, [self.window.PosData[self.window.index+1], self.window.PosData[self.window.index+3], self.window.PosData[self.window.index+2], self.window.PosData[self.window.index+4], self.window.PosData[self.window.index+8], self.window.PosData[self.window.index+9], self.window.PosData[self.window.index+6], self.window.PosData[self.window.index+7]]) #Item name, Number of bitmap, Position within bitmap, Item ID, Damage Type, Attack, Min Damage, Max Damage
                            self.window.index += 11
                        else:
                            self.window.CharactersDict[self.window.CurCharNum].add_data(i, [self.window.PosData[self.window.index+1], self.window.PosData[self.window.index+3], self.window.PosData[self.window.index+2], self.window.PosData[self.window.index+4]]) #Item name, Number of bitmap, Position within bitmap, Item ID
                            self.window.index += 7
                    else:
                        self.window.CharactersDict[self.window.CurCharNum].add_data(i, [self.window.PosData[self.window.index+1]]) # - Nothing Equipped
                        self.window.index += 3
                self.window.CharactersDict[self.window.CurCharNum].add_data("Equipment Names", self.window.EquipmentNames)
   
            if self.window.ShopTest:
                self.window.StoresList = []
                while self.window.PosData[self.window.index] != "Information":
                    self.window.StoresList.append(self.window.PosData[self.window.index])
                    self.window.index += 1
                self.window.CharactersDict[self.window.CurCharNum].add_data("Stores", self.window.StoresList)
            else:
                for i in self.window.BackpackList:
                    if self.window.PosData[self.window.index] == "1":
                        self.window.CharactersDict[self.window.CurCharNum].add_data(i, [self.window.PosData[self.window.index+1], self.window.PosData[self.window.index+3], self.window.PosData[self.window.index+2], self.window.PosData[self.window.index+4], self.window.PosData[self.window.index+5], self.window.PosData[self.window.index+6]]) #Item name, Number of bitmap, Position within bitmap, Item ID, Amount, Slot/Not Equippable
                        self.window.index += 7
                    else:
                        self.window.CharactersDict[self.window.CurCharNum].add_data(i, [self.window.PosData[self.window.index+1]]) #Empty
                        self.window.index += 2
                        
            self.window.CharactersDict[self.window.CurCharNum].add_data("Gold", self.window.PosData[self.window.index+1].split()[1])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Alignment", self.window.PosData[self.window.index+2])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Hostility", self.window.PosData[self.window.index+3].split()[1])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Aggression", "Normal")
            self.window.CharactersDict[self.window.CurCharNum].add_data("Vision", self.window.PosData[self.window.index+4].split()[1])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Move Rate", self.window.PosData[self.window.index+5].split(": ")[1])
            self.window.CharactersDict[self.window.CurCharNum].add_data("HP", self.window.PosData[self.window.index+6])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Attack", self.window.PosData[self.window.index+7].split()[-1])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Experience", self.window.PosData[self.window.index+8].split()[1])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Damage", self.window.PosData[self.window.index+9])
            if self.window.ShopTest:
                self.window.CharactersDict[self.window.CurCharNum].add_data("Last Ate", "N/A")
                self.window.CharactersDict[self.window.CurCharNum].add_data("Last Slept", "N/A")
            else:
                self.window.CharactersDict[self.window.CurCharNum].add_data("Last Ate", self.window.PosData[self.window.index+11].split()[2])
                self.window.CharactersDict[self.window.CurCharNum].add_data("Last Slept", self.window.PosData[self.window.index+12].split()[2])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Fear Factor", self.window.PosData[self.window.index+13].split()[2])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Defences", [self.window.PosData[self.window.index+15].split()[1], self.window.PosData[self.window.index+16].split()[1], self.window.PosData[self.window.index+17].split()[1], self.window.PosData[self.window.index+18].split()[1], self.window.PosData[self.window.index+19].split()[1], self.window.PosData[self.window.index+20].split()[1]]) #Normal, Fire, Cold, Alchemical, Magical, Mental
            self.window.CharactersDict[self.window.CurCharNum].add_data("DamRed", [self.window.PosData[self.window.index+22].split()[1], self.window.PosData[self.window.index+23].split()[1], self.window.PosData[self.window.index+24].split()[1], self.window.PosData[self.window.index+25].split()[1], self.window.PosData[self.window.index+26].split()[1], self.window.PosData[self.window.index+27].split()[1]]) #Normal, Fire, Cold, Alchemical, Magical, Mental
            self.window.CharactersDict[self.window.CurCharNum].add_data("Statistics", [self.window.PosData[self.window.index+29], self.window.PosData[self.window.index+30], self.window.PosData[self.window.index+31], self.window.PosData[self.window.index+32], self.window.PosData[self.window.index+33], self.window.PosData[self.window.index+34]]) #Normally Appearance, Willpower, Dexterity, Strength, Wisdom, Intelligence
            self.window.CharactersDict[self.window.CurCharNum].add_data("Upkeep", self.window.PosData[self.window.index+35])
            self.window.CharactersDict[self.window.CurCharNum].add_data("Owner", self.window.PosData[self.window.index+36])
            if self.window.PosData[self.window.index+37] == "1":
                self.window.CurVision = (int(self.window.PosData[self.window.index+40])+1)/2
                self.window.CharactersDict[self.window.CurCharNum].add_data("XPos", str((int(self.window.PosData[self.window.index+38])+self.window.CurVision-1)%int(self.window.PosData[self.window.index+42])))
                self.window.CharactersDict[self.window.CurCharNum].add_data("YPos", str((int(self.window.PosData[self.window.index+39])+self.window.CurVision-1)%int(self.window.PosData[self.window.index+43])))

                self.window.CurMapWidth = int(self.window.PosData[self.window.index+42])
                self.window.CurMapHeight = int(self.window.PosData[self.window.index+43])
            else:
                self.window.CurVision = 0
                self.window.CharactersDict[self.window.CurCharNum].add_data("XPos", "0")
                self.window.CharactersDict[self.window.CurCharNum].add_data("YPos", "0")
                self.window.CharactersDict[self.window.CurCharNum].add_data("Vision", "0")

                self.window.CurMapWidth = 0
                self.window.CurMapHeight = 0
            

            if self.window.NewMap: #If map didn't exist we create with null data
                self.window.MapsDict[self.window.CurMapName] = GameMap()
                self.window.MapsDict[self.window.CurMapName].DataList = ["0.0" if i % 5 == 0 else "0" for i in range(self.window.CurMapWidth * self.window.CurMapHeight * 5)]
                self.window.MapsDict[self.window.CurMapName].DataList.insert(0, str(self.window.CurMapHeight))
                self.window.MapsDict[self.window.CurMapName].DataList.insert(0, str(self.window.CurMapWidth))

            if self.window.PosData[self.window.index+37] == "1":
                self.window.MapStartX = int(self.window.PosData[self.window.index+38]) #Update terrain data from character map
                self.window.MapStartY = int(self.window.PosData[self.window.index+39])
                self.window.index += 44 
                self.window.TotalMapWidth = int(self.window.PosData[self.window.index-4]) 
                for Y in range(0,self.window.TotalMapWidth):
                    for X in range(0,self.window.TotalMapWidth):
                        self.window.MapDataListStartIndex = (((self.window.MapStartY+Y-1)%self.window.CurMapHeight)*self.window.CurMapWidth+((self.window.MapStartX+X-1)%self.window.CurMapWidth))*5+2
                        if self.window.PosData[self.window.index] == "0":
                            #self.window.MapsDict[self.window.CurMapName].DataList[self.window.MapDataListStartIndex:self.window.MapDataListStartIndex+5] = ['???','0','0','0','0']
                            self.window.index += 1
                        else:
                            self.window.MapsDict[self.window.CurMapName].add_Visible((self.window.MapDataListStartIndex-2)/5)
                            self.window.MapsDict[self.window.CurMapName].DataList[self.window.MapDataListStartIndex:self.window.MapDataListStartIndex+5] = [str(self.window.PosData[self.window.index+1]) + "." + str(self.window.PosData[self.window.index+2]),self.window.PosData[self.window.index+3],self.window.PosData[self.window.index+4],self.window.PosData[self.window.index+7],self.window.PosData[self.window.index+8]] #ID, BMP, BMPPos, Gold, Item
                            self.window.index += 9
            else:
                self.window.index += 36

            if self.window.PosData[self.window.index+1] == "0": #Items in square
                self.LocalItemList = "None"
            else:
                self.LocalItemList = []
                for i in range(0,int(self.window.PosData[self.window.index+1])):
                    self.LocalItems = []
                    self.LocalItems.append(self.window.PosData[self.window.index+(i+1)*2])
                    self.LocalItems.append(self.window.PosData[self.window.index+(i+1)*2+1])
                    self.LocalItemList.append(self.LocalItems)
            self.window.index += int(self.window.PosData[self.window.index+1])*2+2
            if self.LocalItemList != "None":
                self.window.localItems[int(float(self.window.CharactersDict[self.window.CurCharNum].DataDict["XPos"]))+(int(float(self.window.CharactersDict[self.window.CurCharNum].DataDict["YPos"]))-1)*self.window.CurMapWidth] = self.LocalItemList
            #self.window.CharactersDict[self.window.CurCharNum].add_data("LocalItems", self.window.LocalItems)

            self.window.OtherDetailsList = ["<span style='text-decoration: underline; font-size:14pt; font-weight:bold;'> Character Description</span>"] #Sort out descriptions
            self.firstDescription = True
            while self.window.PosData[self.window.index] != "Actions This Turn" and self.window.PosData[self.window.index] != "Business This Turn" and self.window.PosData[self.window.index] != "Events This Turn":
                self.current_description = self.window.PosData[self.window.index]
                if self.window.PosData[self.window.index] == "±":
                    print("Bad")
                if self.firstDescription:
                    self.window.OtherDetailsList.append(f"<br>{self.current_description}<br>")
                    self.firstDescription = False
                else:
                    if self.current_description != "|" and not self.current_description.isdigit():
                        self.window.OtherDetailsList.append(self.current_description)
                self.window.index += 1
            #self.window.CharactersDict[self.window.CurCharNum].add_data("Descriptions", self.window.DescriptionsList)

            if self.window.CurVision != 0:
                self.window.ActionsList = [] #Sort out actions
                self.window.ShiftList = []
                self.window.index += 1
                self.turn_section = "Actions"
                while self.window.PosData[self.window.index] != "Other Characters I Can See" and self.window.PosData[self.window.index] != "Characters Nearby" and self.window.PosData[self.window.index] != "Other Characters Seen":
                    self.addString = self.window.PosData[self.window.index]
                    if self.addString == "@ItemDescription":
                        window.saved_item_data[self.window.PosData[self.window.index+1]] = {"description_1": self.window.PosData[self.window.index+3], "description_2": "", "orders": [{"order": "! 0 0", "description": ""}, {"order": "! 0 0", "description": ""}, {"order": "! 0 0", "description": ""}, {"order": "! 0 0", "description": ""}, {"order": "! 0 0", "description": ""}]}

                    if self.addString == "@MasterForceDescription":
                        window.saved_creature_data[self.window.PosData[self.window.index+1]] = self.window.PosData[self.window.index+3]
                    
                    if self.turn_section == "Actions" or self.turn_section == "Phase 15":
                        if self.turn_section == "Phase 15" and self.addString == " ":
                            self.turn_section = "Shifts"
                        elif not self.addString.isdigit() and self.addString != "|" and self.addString.strip() != "":
                            if "Start of Phase" in self.addString:
                                self.window.ActionsList.append(f"<br>&nbsp;{self.addString}")
                                if self.addString == " Start of Phase 15":
                                    self.turn_section = "Phase 15"
                            else:
                                #Isolate orders from the string
                                self.search_pattern = r'([A-Za-z] \d+ \d+)'
                                self.result = []
                                self.last_end = 0
                                for match in re.finditer(self.search_pattern, self.addString):
                                    if match.start() > self.last_end:
                                        self.result.append(("text", self.addString[self.last_end:match.start()]))
                                    self.result.append(("match", match.group()))
                                    self.last_end = match.end()
                                if self.last_end < len(self.addString):
                                    self.result.append(("text", self.addString[self.last_end:]))
                                for label, part in self.result:
                                    if label == "match":
                                        self.window.ActionsList.append(f"<br><span style='font-size:12pt; font-weight:bold;'> {part}</span>")
                                    elif "@" in part:
                                        if part == "@":
                                            self.window.ActionsList.append("")
                                    else:
                                        self.window.ActionsList.append(part)
                    else:
                        self.window.ShiftList.append(self.addString)
                    self.window.index += 1
                self.window.CharactersDict[self.window.CurCharNum].add_data("Actions", self.window.ActionsList)
                self.window.CharactersDict[self.window.CurCharNum].add_data("Shifts", self.window.ShiftList)

                self.window.index += 1 #Sort out visible characters
                
                while self.window.PosData[self.window.index] != "0":
                    self.window.MapsDict[self.window.CurMapName].add_Character(int(self.window.PosData[self.window.index+7])+(int(self.window.PosData[self.window.index+8])-1)*self.window.CurMapWidth,(self.window.PosData[self.window.index+1],self.window.PosData[self.window.index+2],self.window.PosData[self.window.index+3],self.window.PosData[self.window.index+4],self.window.PosData[self.window.index+5],self.window.PosData[self.window.index+6])) #Class, Name, RIP, BMPNum, BMPPos, ID
                    self.window.index += 9
                self.window.index += 1

            #Sort out rest of other details
            self.window.CurDataPoint = self.window.PosData[self.window.index]
            self.NextPoint = "None"
            while self.window.CurDataPoint != "±" and self.window.CurDataPoint != "@":
                if self.window.CurDataPoint == "Defensive":
                    self.window.CharactersDict[self.window.CurCharNum].DataDict["Aggression"] = "Defensive"
                elif self.window.CurDataPoint == "Gung-Ho":
                    self.window.CharactersDict[self.window.CurCharNum].DataDict["Aggression"] = "Gung-Ho"

                
                if self.window.CurDataPoint == "General Info" or self.window.CurDataPoint == "Defence" or self.window.CurDataPoint == "Special Conditions" or "Path" in self.window.CurDataPoint or self.window.CurDataPoint == "Public Info" or self.window.CurDataPoint == "Castle Specialities" or self.window.CurDataPoint == "Magical Defences" or self.window.CurDataPoint == "Castle Improvements":
                    self.window.OtherDetailsList.append(f"<br><span style='text-decoration: underline; font-size:14pt; font-weight:bold;'> {self.window.CurDataPoint}</span><br>")
                    self.NextPoint = "None"
                    if self.window.CurDataPoint == "General Info":
                        if self.window.CharactersDict[self.window.CurCharNum].DataDict['Upkeep'] != '0 ':
                            self.window.OtherDetailsList.append(f"Owner: {self.window.CharactersDict[self.window.CurCharNum].DataDict['Owner']}")
                            self.window.OtherDetailsList.append(f"Upkeep: {self.window.CharactersDict[self.window.CurCharNum].DataDict['Upkeep']}")
                elif self.window.CurDataPoint == "Specialised Skills" or self.window.CurDataPoint == "Shifts" or self.window.CurDataPoint == "Tattoos, Marks & Piercing" or self.window.CurDataPoint == "Magical Effects" or self.window.CurDataPoint == "Titles & Awards" or self.window.CurDataPoint == "Powers / Boons / Secrets":
                    self.window.OtherDetailsList.append(f"<br><span style='text-decoration: underline; font-size:14pt; font-weight:bold;'> {self.window.CurDataPoint}</span>")
                    if self.window.CurDataPoint == "Shifts":
                        self.NextPoint = "Shifts"
                    elif self.window.CurDataPoint == "Tattoos, Marks & Piercing":
                        self.NextPoint = "Tattoos"
                    elif self.window.CurDataPoint == "Magical Effects":
                        self.NextPoint = "Magical Effects"
                        self.NewEffect = True
                    elif self.window.CurDataPoint == "Titles & Awards":
                        self.NextPoint = "Titles"
                    elif self.window.CurDataPoint == "Powers / Boons / Secrets":
                        self.NextPoint = "Powers / Boons / Secrets"
                    elif self.window.CurDataPoint == "Specialised Skills":
                        self.NextPoint = "Skills"
                    else:
                        self.NextPoint = "None"
                elif self.NextPoint == "Shifts":
                    self.NextPoint = "None"
                    self.shift_list = re.split(r'(?<=[a-z0-9])(?=[A-Z"])', self.window.CurDataPoint)
                    for i in self.shift_list:
                        self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {i}:-</span>")
                        for j in range(0, len(self.window.ShiftList)):
                            if i in self.window.ShiftList[j]:
                                self.window.OtherDetailsList.append(f"<span style='font-style: italic;'> {self.window.ShiftList[j+1]}</span>")
                                self.window.OtherDetailsList.append(f"<span style='font-style: italic;'> {self.window.ShiftList[j+2]}</span><br>")
                                self.window.OtherDetailsList.append(self.window.ShiftList[j+3].replace("<", ""))
                                break
                elif self.NextPoint == "Magical Effects":
                    if "None at this time." in self.window.CurDataPoint:
                        self.window.OtherDetailsList.append(f"<br>{self.window.CurDataPoint}")
                        self.NextPoint = "None"
                    elif self.NewEffect:
                        match = re.search(r'(?<=[a-z0-9])(?=[A-Z"])', self.window.CurDataPoint)
                        if match:
                            self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {self.window.CurDataPoint[:match.start()].strip()}</span>")
                            self.window.OtherDetailsList.append(f"{self.window.CurDataPoint[match.start():].strip()}")
                        else:
                            self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {self.window.CurDataPoint}</span>")
                        self.NewEffect = False
                    elif self.window.CurDataPoint == "":
                        self.NewEffect = True
                    else:
                        self.window.OtherDetailsList.append(self.window.CurDataPoint)
                elif not self.window.CurDataPoint.isdigit() and self.window.CurDataPoint != "|" and self.window.CurDataPoint.strip() != "":
                    if self.NextPoint == "Skills":
                        if "None at this time." in self.window.CurDataPoint:
                            self.window.OtherDetailsList.append(f"<br>{self.window.CurDataPoint}")
                            self.NextPoint = "None"
                        else:
                            self.PreSkill = "Skill: "
                            if "PreSkill" in self.window.CurDataPoint:
                                self.window.CurDataPoint = self.window.CurDataPoint[len("PreSkill: "):]
                                self.PreSkill = "PreSkill: "
                            elif "Undead Skill" in self.window.CurDataPoint:
                                self.window.CurDataPoint = self.window.CurDataPoint[len("Undead Skill: "):]
                                self.PreSkill = "Undead Skill: "                                
                            elif "Skill" in self.window.CurDataPoint:
                                self.window.CurDataPoint = self.window.CurDataPoint[len("Skill: "):]
                            #print(f"{self.window.CurDataPoint}\n")
                            match = re.search(r'(?<=[a-z0-9()])(?=[A-Z"])', self.window.CurDataPoint)
                            if match:
                                self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {self.PreSkill}{self.window.CurDataPoint[:match.start()].strip()}</span>")
                                self.window.OtherDetailsList.append(f"{self.window.CurDataPoint[match.start():].strip()}")
                            else:
                                self.window.OtherDetailsList.append(self.window.CurDataPoint.strip())
                    elif self.NextPoint == "Tattoos" or self.NextPoint == "Titles" or self.NextPoint == "Powers / Boons / Secrets":
                        match = re.search(r'(?<=[a-z0-9)])(?=[A-Z"])', self.window.CurDataPoint)
                        #print(f"{self.window.CurDataPoint}\n")
                        if match:
                            self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {self.window.CurDataPoint[:match.start()].strip()}</span>")
                            self.window.OtherDetailsList.append(f"{self.window.CurDataPoint[match.start():].strip()}")
                        else:
                            if self.NextPoint == "Titles":
                                pass
                            else:
                                self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {self.window.CurDataPoint.strip()}</span>")
                    else:
                        if "Skill" in self.window.CurDataPoint:
                            self.window.OtherDetailsList.append(f"<br><span style='font-size:10pt; font-weight:bold;'> {self.window.CurDataPoint}</span>")
                        else:
                            self.window.OtherDetailsList.append(self.window.CurDataPoint)
                self.window.index += 1
                self.window.CurDataPoint = self.window.PosData[self.window.index]
            self.window.CharactersDict[self.window.CurCharNum].add_data("Other Details", self.window.OtherDetailsList)
            self.window.count+=1

            #Ensure the character itself is added to visible characters (things like necromancers) if currently invisible
            self.window.MapsDict[self.window.CurMapName].add_Character(int(float(self.window.CharactersDict[self.window.CurCharNum].DataDict["XPos"]))+(int(float(self.window.CharactersDict[self.window.CurCharNum].DataDict["YPos"]))-1)*self.window.CurMapWidth,(self.window.CharactersDict[self.window.CurCharNum].DataDict["Class"],self.window.CharactersDict[self.window.CurCharNum].DataDict["Name"],"",self.window.CharactersDict[self.window.CurCharNum].DataDict["CharGraphic"][1],self.window.CharactersDict[self.window.CurCharNum].DataDict["CharGraphic"][0],self.window.CharactersDict[self.window.CurCharNum].DataDict["Number"])) #Class, Name, RIP, BMPNum, BMPPos, ID

            if self.window.PosData[self.window.index] == "@":
                break

        try:
            self.label_updated.emit(f"Updating terrain data")
            self.progress_updated.emit(95)
        except:
            pass
            
        self.window.TerrainKeys = {'???': '0^0^Absolute Nothingness^MPs: ???^Vis. Adj.: ???^Att. Adj.: ???^Def. Adj.: ???'} #Dictionary for terrain list
        #with open('Data/TerrainList.txt', encoding='utf-8') as f: 
            #self.window.TerrainData = f.readlines()
        #for i in self.window.TerrainData:
            #self.window.TerrainKeys[i.split(" - ")[0]] = i.split(" - ")[1].strip()
        terrainData = load_encrypted_text("Data/TerrainList.txt", "Data/TerrainList.dat", EncKey)
        if terrainData:
            for line in terrainData.splitlines():
                try:
                    key, value = line.split(" - ")
                    self.window.TerrainKeys[key] = value.strip()
                except:
                    pass

        for i in range(0,int(self.window.PosData[self.window.index+1])): #Add new terrain to keys
            self.window.IDKey = str(self.window.PosData[self.window.index+6+i*10]) + "." + str(self.window.PosData[self.window.index+7+i*10])
            self.window.TerrainKeys[self.window.IDKey] = self.window.PosData[self.window.index+9+i*10] + "^" + self.window.PosData[self.window.index+8+i*10] + "^" + self.window.PosData[self.window.index+10+i*10] + "^" + self.window.PosData[self.window.index+12+i*10] + "^" + self.window.PosData[self.window.index+13+i*10] + "^" + self.window.PosData[self.window.index+14+i*10] + "^" + self.window.PosData[self.window.index+15+i*10] #ID, BMP, BMPPos, Name, MPs, Vis, Att, Def

        #with open('Data/TerrainList.txt', 'w', encoding='utf-8') as file: #Save back to file in case new keys were added
            #for key, value in self.window.TerrainKeys.items():
                #file.write(f"{key} - {value}\n")
        lines = [f"{key} - {value}" for key, value in self.window.TerrainKeys.items()]
        data = "\n".join(lines)
        save_encrypted_text(data, 'Data/TerrainList.dat', EncKey)

        with open('Data/Class Order.txt', 'w', encoding='utf-8') as file:
            file.write('\n'.join(window.ClassOrder))

        try:
            self.label_updated.emit(f"Saving map data")
            self.progress_updated.emit(97)
        except:
            pass

        try:
            window.saved_item_data = dict(sorted(window.saved_item_data.items()))
        except:
            window.saved_item_data = {}
        #with open("Data/Information/Items.json", 'w', encoding='utf-8') as file:
            #json.dump(window.saved_item_data, file, indent=4, ensure_ascii=False)
        save_encrypted_json(window.saved_item_data, "Data/Information/Items.dat", EncKey)

        try:
            window.saved_creature_data = dict(sorted(window.saved_creature_data.items()))
        except:
            window.saved_creature_data = {}
        #with open("Data/Information/Creatures.json", 'w', encoding='utf-8') as file:
            #json.dump(window.saved_creature_data, file, indent=4, ensure_ascii=False)
        save_encrypted_json(window.saved_creature_data, "Data/Information/Creatures.dat", EncKey)
                
        self.finished.emit()

class LetterEditFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Backspace:
                if self.handle_backspace(obj):
                    return True
        return False

    def handle_backspace(self, line_edit):
        for i in range(3,43):
            if window.OrderEditsList[i].objectName() == line_edit.objectName():
                if window.OrderEditsList[i].text() == "":
                    window.OrderEditsList[i-1].setFocus()
                    return True
        return False

class NumberEditFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if isinstance(obj, QtWidgets.QLineEdit) and event.text().isalpha():
                self.handle_letter_key(obj, event.text())
                return True
            elif event.key() == QtCore.Qt.Key.Key_Backspace:
                if self.handle_backspace(obj):
                    return True
        return False

    def handle_letter_key(self, line_edit, letter):
        for i in range(0,42):
            if window.OrderEditsList[i].objectName() == line_edit.objectName():
                self.nextLetterIndex = ((i//3) + 1) * 3
                if window.OrderEditsList[self.nextLetterIndex].isEnabled():
                    window.OrderEditsList[self.nextLetterIndex].blockSignals(True)
                    window.OrderEditsList[self.nextLetterIndex].setText(letter.upper())
                    window.OrderEditsList[self.nextLetterIndex].blockSignals(False)
                    window.OrderEditsList[self.nextLetterIndex+1].setFocus()
                    window.OrderEditsList[self.nextLetterIndex+1].selectAll()
                    window.render_movement()
                break

    def handle_backspace(self, line_edit):
        for i in range(1,45):
            if window.OrderEditsList[i].objectName() == line_edit.objectName():
                if window.OrderEditsList[i].text() == "":
                    window.OrderEditsList[i-1].setFocus()
                    return True
        return False

class ClickableLinkFilter(QtCore.QObject):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.Enter:
            watched.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                webbrowser.open(self.url)
        return False

class ClickableItemFilter(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.Enter:
            watched.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                if watched in window.EquipmentIconList:
                    idx = window.EquipmentIconList.index(watched)
                    ItemName = window.EquipmentLabelsList[idx].text()
                else:
                    idx = window.BackpackIconList.index(watched)
                    ItemName = window.BackpackLabelsList[idx].text()
                if ItemName in list(window.saved_item_data.keys()):
                    window.open_itemLibrary()
                    index = window.itemLibraryWindow.ItemsListBox.findText(ItemName)
                    if index != -1:
                        window.itemLibraryWindow.ItemsListBox.setCurrentIndex(index)
        return False

class ItemFocusFilter(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.WindowActivate:
            window.ActiveItemHighlight = True
            try:
                self.focused_Order = int(window.OrderEditsList.index(window.focus_tracker.last_focused_widget)/3)
            except:
                self.focused_Order = 0
            self.writeLetterIndex = self.focused_Order * 3
            window.OrderEditsList[self.writeLetterIndex].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            window.OrderEditsList[self.writeLetterIndex+1].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            window.OrderEditsList[self.writeLetterIndex+2].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            
        elif event.type() == QtCore.QEvent.Type.WindowDeactivate:
            window.ActiveItemHighlight = False
            if not window.ActiveItemHighlight and not window.ActiveSkillHighlight:
                try:
                    self.focused_Order = int(window.OrderEditsList.index(window.focus_tracker.last_focused_widget)/3)
                except:
                    self.focused_Order = 0
                self.writeLetterIndex = self.focused_Order * 3
                window.OrderEditsList[self.writeLetterIndex].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+1].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+2].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
        return False

class SkillFocusFilter(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.WindowActivate:
            window.ActiveSkillHighlight = True
            try:
                self.focused_Order = int(window.OrderEditsList.index(window.focus_tracker.last_focused_widget)/3)
            except:
                self.focused_Order = 0
            self.writeLetterIndex = self.focused_Order * 3
            window.OrderEditsList[self.writeLetterIndex].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            window.OrderEditsList[self.writeLetterIndex+1].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            window.OrderEditsList[self.writeLetterIndex+2].setStyleSheet("QLineEdit { padding: 1px; background-color: #97C6EB; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            
        elif event.type() == QtCore.QEvent.Type.WindowDeactivate:
            window.ActiveSkillHighlight = False
            if not window.ActiveItemHighlight and not window.ActiveSkillHighlight:
                try:
                    self.focused_Order = int(window.OrderEditsList.index(window.focus_tracker.last_focused_widget)/3)
                except:
                    self.focused_Order = 0
                self.writeLetterIndex = self.focused_Order * 3
                window.OrderEditsList[self.writeLetterIndex].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+1].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
                window.OrderEditsList[self.writeLetterIndex+2].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
        return False


class OrderPopup(QtWidgets.QMainWindow, Ui_ViewTurn):
    """Create and handle the order popup application."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Create the application, set text to current strings, change the icon and connect the buttons."""
        super(OrderPopup, self).__init__(*args, **kwargs) #Setup UI as defined in Standard Scroll Screen UI script.
        self.setupUi(self)

        letter = window.letter

        self.HeaderLabel.setText(f"Orders - {letter}")

        self.CloseButton.clicked.connect(self.ExitOrderView)
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon

        file_path = f"Data/Information/Order Descriptions/{letter}.txt"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.TextDisplay.setText(f.read())
        except FileNotFoundError:
            self.TextDisplay.setText(f"File '{file_path}' not found.")

    def ExitOrderView(self):
        """Close the window."""
        self.close()

class DownloadWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(str, int)
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, pos):
        super().__init__()
        self.pos = pos

    def run(self):
        try:
            final_path = f"Data/NVE Files/Player{self.pos}.nve"
            temp_path = final_path + ".tmp"

            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            def callback(transferred, total):
                percent = int((transferred / total) * 100)
                self.progress.emit(self.pos, percent)

            sftp.get(
                f"/PrintFile{self.pos}.nve",
                temp_path,
                callback=callback
            )

            sftp.close()
            transport.close()

            os.replace(temp_path, final_path)

            self.finished.emit(self.pos)

        except:
            self.error.emit(self.pos)

class DownloadManager(QtCore.QObject):

    download_finished = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.queue = deque()
        self.active = False

    def add_download(self, pos, selected_item):
        self.queue.append((pos, selected_item))
        if not self.active:
            self.start_next()

    def start_next(self):
        if not self.queue:
            self.active = False
            window.CloseNVEButton.setEnabled(True)
            window.ViewNVEButton.setEnabled(True)
            window.MoveUpButton.setEnabled(True)
            window.MoveDownButton.setEnabled(True)
            window.DownloadNVEButton.setEnabled(True)
            window.DownloadPDFButton.setEnabled(True)
            window.ViewPDFButton.setEnabled(True)
            return

        self.active = True
        pos, selected_item = self.queue.popleft()

        self.thread = QtCore.QThread()
        self.worker = DownloadWorker(pos)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.progress.connect(
            lambda p, percent:
            selected_item.setText(
                f"DungeonWorld Game 5 Player {p}: Downloading NVE - {percent}%"
            )
        )

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda p: self.on_finished(p, selected_item))

        self.thread.start()

    def on_finished(self, pos, selected_item):
        with open('Data/NVE Files/Player'+pos+'.nve', 'r') as f: #Reads in all data from the nve file and splits it by the carats, will need to take this out of memory once processed as it can be quite big.
            window.PosData = f.read().split('^')
        window.PosNumberDict[pos] = window.PosData[0]
        window.LastSentDict[pos] = "Not sent" #LastSentDict
        with open('Data/Last Sent.txt', 'w') as file:
            for key, value in window.LastSentDict.items():
                file.write(f"{key} - {value}\n")
        if os.path.exists("Data/Messages/DungeonWorld5-" + pos + "dun-msg"): #Also remove messages on new turn.
          os.remove("Data/Messages/DungeonWorld5-" + pos + "dun-msg")

        char_nums = [window.PosData[i+4] for i, val in enumerate(window.PosData) if val == "±"]

        for i in char_nums:
            try: #Copy orders to last turn if they exist and then delete the current orders file
                shutil.copy("Data/Current Orders/" + i, "Data/Last Orders/" + i)
                if i not in window.AutoLoadDict[pos]:
                    os.remove("Data/Current Orders/" + i)
            except:
                pass
            
        with open('Data/Position Numbers.txt', 'w') as file:
            for key, value in window.PosNumberDict.items():
                file.write(f"{key} - {value}\n")            
        selected_item.setText(
            f"DungeonWorld Game 5 Player {pos}: {window.LastSentDict[pos]}"
        )
        self.active = False
        self.download_finished.emit(pos)
        self.start_next()

class PDFDownloadWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(str, int)
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, pos):
        super().__init__()
        self.pos = pos

    def run(self):
        try:
            final_path = f"Data/PDFs/Player{self.pos}.pdf"
            temp_path = final_path + ".tmp"

            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            def callback(transferred, total):
                percent = int((transferred / total) * 100)
                self.progress.emit(self.pos, percent)

            if window.CorrectPDFPath:
                sftp.get(
                    f"/PDFs/PostScript{str(window.pdf_dict[str(self.pos)])}.PDF",
                    temp_path,
                    callback=callback
                )
            else:
                sftp.get(
                    f"/PostScript{str(window.pdf_dict[str(self.pos)])}.PDF",
                    temp_path,
                    callback=callback
                )

            sftp.close()
            transport.close()

            os.replace(temp_path, final_path)

            self.finished.emit(self.pos)

        except:
            self.error.emit(self.pos)

class PDFDownloadManager(QtCore.QObject):

    download_finished = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.queue = deque()
        self.active = False

    def add_download(self, pos, selected_item):
        self.queue.append((pos, selected_item))
        if not self.active:
            self.start_next()

    def start_next(self):
        if not self.queue:
            self.active = False
            window.CloseNVEButton.setEnabled(True)
            window.ViewNVEButton.setEnabled(True)
            window.MoveUpButton.setEnabled(True)
            window.MoveDownButton.setEnabled(True)
            window.DownloadNVEButton.setEnabled(True)
            window.DownloadPDFButton.setEnabled(True)
            window.ViewPDFButton.setEnabled(True)
            return

        self.active = True
        pos, selected_item = self.queue.popleft()

        self.thread = QtCore.QThread()
        self.worker = PDFDownloadWorker(pos)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.progress.connect(
            lambda p, percent:
            selected_item.setText(
                f"DungeonWorld Game 5 Player {p}: Downloading PDF - {percent}%"
            )
        )

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda p: self.on_finished(p, selected_item))

        self.thread.start()

    def on_finished(self, pos, selected_item):           
        #selected_item.setText(
            #f"DungeonWorld Game 5 Player {pos}: {window.LastSentDict[pos]}"
        #)
        if window.NewTurnNum != window.PosNumberDict[pos] and window.NewTurnNum != "":
            selected_item.setText(f"DungeonWorld Game 5 Player {pos}: New turn available")
        else:
            selected_item.setText(f"DungeonWorld Game 5 Player {pos}: {window.LastSentDict[pos]}")
        self.active = False
        self.download_finished.emit(pos)
        self.start_next()        

def save_encrypted_json(data, filename, key):

    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")

    encrypted = encrypt_bytes(raw, key)

    with open(filename, "wb") as f:
        f.write(encrypted)

def save_encrypted_text(text, filename, key):

    encrypted = encrypt_bytes(text.encode("utf-8"), key)

    with open(filename, "wb") as f:
        f.write(encrypted)

def load_encrypted_text(txt_name, dat_name, key):
    if os.path.exists(dat_name):
        with open(dat_name, "rb") as f:
            encrypted = f.read()
        decrypted = decrypt_bytes(encrypted, key)
        return decrypted.decode("utf-8")

    elif os.path.exists(txt_name):
        with open(txt_name, "r", encoding="utf-8") as f:
            data = f.read()
        save_encrypted_text(data, dat_name, key)
        os.remove(txt_name)
        return data

    else:
        return {}      

def load_encrypted_json(json_name, dat_name, key):

    if os.path.exists(dat_name):
        with open(dat_name, "rb") as f:
            encrypted = f.read()
        raw = decrypt_bytes(encrypted, key)
        return json.loads(raw.decode("utf-8")) 

    elif os.path.exists(json_name):
        with open(json_name, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = ''
        save_encrypted_json(data, dat_name, key)
        os.remove(json_name)
        return data

    else:
        return {}    

       

class MainWindow(QtWidgets.QMainWindow, Ui_NVE2POINT0):
    """Class to handle the main GUI including most program functionality."""
    
    def __init__(self, *args, obj=None, **kwargs):
        """Connect buttons and set variables upon program launch. Also add required event filters, validators and set the blank icons.

        Variables:
        self.PosNumberDict - Dictionary containing string keys of each position number, and a string when they were last loaded as values, the value represents a number which counts up each turn.
        self.AutoLoadDict - Dictionary containing string keys of each position number, and a list of string character numbers as values for which auto load is enabled.
        self.NVEPath - The path to the old NVE (folder containing .exe)
        A number of lists for various things that can be iterated through to make code more readable - most are lists of ui elements.
        self.blank_icon - Reference to pixmap used for blank icons.
        self.PositionLoaded - Boolean for whether a position is currently loaded.
        self.CurLoadedMap - String containing the currently loaded map name, or "" if none is loaded.
        """
        super(MainWindow, self).__init__(*args, **kwargs) #Setup UI as defined in Main Window UI script.
        self.setupUi(self)

        #-----Connect widgets-----
        self.CloseNVEButton.clicked.connect(QtWidgets.QApplication.quit) # Main menu buttons
        self.SettingsButtonMainMenu.clicked.connect(self.open_settings)
        self.ViewNVEButton.clicked.connect(self.main_load_position)
        self.DownloadNVEButton.clicked.connect(self.main_download_pos)
        self.DownloadPDFButton.clicked.connect(self.main_download_pdf)
        self.ViewPDFButton.clicked.connect(self.view_pdf)
        self.MoveUpButton.clicked.connect(self.MovePosUp) 
        self.MoveDownButton.clicked.connect(self.MovePosDown) 
        
        self.ChangePositionButton.clicked.connect(self.AskPosition) # Loaded position buttons
        self.LastCharacterButton.clicked.connect(self.LastCharacter)
        self.NextCharacterButton.clicked.connect(self.NextCharacter)
        self.FindCharacterButton.clicked.connect(self.FindCharacter)
        self.SendOrdersButton.clicked.connect(self.BuildOrders)
        self.LoadAllLastOrdersButton.clicked.connect(self.LoadAllLast)
        self.LoadCharacterLastOrdersButton.clicked.connect(self.LoadCurLast)
        self.EraseCurrentOrderButton.clicked.connect(self.EraseOrder)
        self.AutoLoadLastOrders.stateChanged.connect(self.UpdateAutoLast)
        self.CopyCurrentOrderButton.clicked.connect(self.CopyCurrentDown)
        self.EraseOrdersButton.clicked.connect(self.EraseAll)
        self.MoveDownButton_2.clicked.connect(self.MoveAllDown)
        self.CopyOrderToEndButton.clicked.connect(self.CopyToEnd)
        self.EraseOrderButton.clicked.connect(self.EraseMoveUp)
        self.WriteMessagesButton.clicked.connect(self.write_message)
        self.ViewMessagesButton.clicked.connect(self.view_messages)
        self.ViewTurnButton.clicked.connect(self.view_turn)
        self.OtherDetailsButton.clicked.connect(self.view_other_details)
        self.SettingsButton.clicked.connect(self.open_settings)
        self.ExitToMainMenuButton.clicked.connect(self.load_main_menu)
        self.ToggleGoldButton.clicked.connect(self.toggleGold)
        self.ToggleItemButton.clicked.connect(self.toggleItems)
        self.ToggleCharacterButton.clicked.connect(self.toggleChars) 
        self.ToggleShadersButton.clicked.connect(self.toggleShaders)
        self.ItemsButton.clicked.connect(self.open_itemLibrary)
        self.CreaturesButton.clicked.connect(self.open_creatureLibrary)
        self.CentreMapButton.clicked.connect(self.centreMap)
        self.SkillsButton.clicked.connect(self.open_skillLibrary)

        for letter in map(chr, range(ord('A'), ord('Z') + 1)):
            btn_name = f"Button{letter}"
            button = getattr(self, btn_name, None)
            if button:
                button.clicked.connect(lambda _, l=letter: self.show_orderWindow(l))

        self.CharactersCreatures_2.activated.connect(self.SelectLoad)
        self.Items.activated.connect(self.SelectItem)

        #-----Set Generic Variables-----
        with open('Data/Position Numbers.txt') as f:
            self.NumsData = f.readlines()
        self.PosNumberDict = {}
        for i in self.NumsData:
            self.PosNumberDict[i.split(" - ")[0]] = i.split(" - ")[1].strip()

        if not os.path.exists('Data/Last Sent.txt'):
            with open('Data/Last Sent.txt', 'w') as file:
                for key, value in self.PosNumberDict.items():
                    file.write(f"{key} - Not sent\n")

        with open('Data/Last Sent.txt') as f:
            self.SentData = f.readlines()
        self.LastSentDict = {}
        for i in self.SentData:
            self.LastSentDict[i.split(" - ")[0]] = i.split(" - ")[1].strip()
            
        with open('Data/AutoLoad.txt') as f:
            self.AutoLoadData = f.readlines()
        self.AutoLoadDict = {}
        for i in self.AutoLoadData:
            self.AutoLoadDict[i.split(" - ")[0]] = i.split(" - ")[1].strip().split()

        try:
            with open('Data/Class Order.txt') as f:
                self.ClassOrder = f.readlines()
            for i in range(0, len(self.ClassOrder)):
                self.ClassOrder[i] = self.ClassOrder[i].strip()
        except:
            self.ClassOrder = []

        #self.saved_item_data = {}
        #if os.path.exists('Data/Information/Items.json'):
            #with open('Data/Information/Items.json', 'r', encoding='utf-8') as f:
                #self.saved_item_data = json.load(f)
        self.saved_item_data = load_encrypted_json("Data/Information/Items.json", "Data/Information/Items.dat", EncKey)


        #self.saved_skill_data = {}
        #if os.path.exists("Data/Information/Skills.json"):
            #with open("Data/Information/Skills.json", "r", encoding="utf-8") as f:
                #self.saved_skill_data = json.load(f)
        self.saved_skill_data = load_encrypted_json("Data/Information/Skills.json", "Data/Information/Skills.dat", EncKey)

        #self.saved_creature_data = {}
        #if os.path.exists('Data/Information/Creatures.json'):
            #with open('Data/Information/Creatures.json', 'r', encoding='utf-8') as f:
                #self.saved_creature_data = json.load(f)
        self.saved_creature_data = load_encrypted_json("Data/Information/Creatures.json", "Data/Information/Creatures.dat", EncKey)
            
        self.EquipmentIconList = [self.HeadIcon, self.NeckIcon, self.BodyIcon, self.WaistIcon, self.LegsIcon, self.FeetIcon, self.In_OnIcon, self.OverBodyIcon, self.OverHandIcon, self.FingerIcon, self.BackIcon, self.LeftArmIcon, self.RightArmIcon, self.AttackHandIcon, self.NotUsedIcon, self.DefenceHandIcon]
        self.BackpackIconList = [self.BP1Icon, self.BP2Icon, self.BP3Icon, self.BP4Icon, self.BP5Icon, self.BP6Icon, self.BP7Icon, self.BP8Icon, self.BP9Icon, self.BP10Icon, self.BP11Icon, self.BP12Icon, self.BP13Icon, self.BP14Icon, self.BP15Icon, self.BP16Icon, self.BP17Icon, self.BP18Icon, self.BP19Icon, self.BP20Icon]
        self.SlotList = ["Head", "Neck", "Body", "Waist", "Legs", "Feet", "In_On", "Over Body", "Over Hand", "Finger", "Back", "Left Arm", "Right Arm", "Attack Hand", "Not Used", "Defence Hand"]
        self.BackpackList = ["Backpack Slot "+str(i) for i in range(1,21)]
        self.EquipmentLabelsList = [self.HeadItem, self.NeckItem, self.BodyItem, self.WaistItem, self.LegsItem, self.FeetItem, self.In_OnItem, self.OverBodyItem, self.OverHandItem, self.FingerItem, self.BackItem, self.LeftArmItem, self.RightArmItem, self.AttackHandItem, self.NotUsedItem, self.DefenceHandItem]
        self.BackpackLabelsList = [self.BP1ItemLabel, self.BP2ItemLabel, self.BP3ItemLabel, self.BP4ItemLabel, self.BP5ItemLabel, self.BP6ItemLabel, self.BP7ItemLabel, self.BP8ItemLabel, self.BP9ItemLabel, self.BP10ItemLabel, self.BP11ItemLabel, self.BP12ItemLabel, self.BP13ItemLabel, self.BP14ItemLabel, self.BP15ItemLabel, self.BP16ItemLabel, self.BP17ItemLabel, self.BP18ItemLabel, self.BP19ItemLabel, self.BP20ItemLabel]
        self.BackpackQuantityList = [self.BP1QuantityValue, self.BP2QuantityValue, self.BP3QuantityValue, self.BP4QuantityValue, self.BP5QuantityValue, self.BP6QuantityValue, self.BP7QuantityValue, self.BP8QuantityValue, self.BP9QuantityValue, self.BP10QuantityValue, self.BP11QuantityValue, self.BP12QuantityValue, self.BP13QuantityValue, self.BP14QuantityValue, self.BP15QuantityValue, self.BP16QuantityValue, self.BP17QuantityValue, self.BP18QuantityValue, self.BP19QuantityValue, self.BP20QuantityValue]
        self.StaffList = ["Steward", "Treasurer", "Stablemaster", "Other Staff", "Chaplain", "Jester", "Lord", "Storemaster", "Butler", "Stonemason", "Carpenter", "Cook", "Guard Captain", "Archers", "Not Used", "Reeve"]
        self.EquipmentHeadersList = [self.HeadLabel, self.NeckLabel, self.BodyLabel, self.WaistLabel, self.LegsLabel, self.FeetLabel, self.In_OnLabel, self.OverBodyLabel, self.OverHandLabel, self.FingerLabel, self.BackLabel, self.LeftArmLabel, self.RightArmLabel, self.AttackHandLabel, self.NotUsedLabel, self.DefenceHandLabel]
        self.StatLabelList = [self.AppearanceLabel, self.WillpowerLabel, self.DexterityLabel, self.StrengthLabel, self.WisdomLabel, self.IntelligenceLabel]
        self.StatValueList = [self.AppearanceValue, self.WillpowerValue, self.DexterityValue, self.StrengthValue, self.WisdomValue, self.IntelligenceValue]
        self.DefenceLabelList = [self.NormalValue, self.FireValue, self.ColdValue, self.AlchemicalValue, self.MagicalValue, self.MentalValue]
        self.OrderEditsList = [self.Order0101, self.Order0102, self.Order0103, self.Order0201, self.Order0202, self.Order0203, self.Order0301, self.Order0302, self.Order0303, self.Order0401, self.Order0402, self.Order0403, self.Order0501, self.Order0502, self.Order0503, self.Order0601, self.Order0602, self.Order0603, self.Order0701, self.Order0702, self.Order0703, self.Order0801, self.Order0802, self.Order0803, self.Order0901, self.Order0902, self.Order0903, self.Order1001, self.Order1002, self.Order1003, self.Order1101, self.Order1102, self.Order1103, self.Order1201, self.Order1202, self.Order1203, self.Order1301, self.Order1302, self.Order1303, self.Order1401, self.Order1402, self.Order1403, self.Order1501, self.Order1502, self.Order1503]    

        self.blank_icon = QtGui.QPixmap("Resources/Program Graphics/Blank Icon.bmp")
        self.madhouse_icon = QtGui.QPixmap("Resources/Program Graphics/logo1.bmp")
        self.hurstnet_icon = QtGui.QPixmap("Resources/Program Graphics/HurstNetIcon50x50.bmp")
        self.madhouse_banner = QtGui.QPixmap("Resources/Program Graphics/Logo2.bmp")
        self.DW_title = QtGui.QPixmap("Resources/Program Graphics/DWDungeonworld.png")
        self.rogue_image = QtGui.QPixmap("Resources/Program Graphics/DWRogue3.png")
        self.main_image = QtGui.QPixmap("Resources/Program Graphics/dwcoloursmallexpanded.png")
        self.PositionLoaded = False
        self.CurLoadedMap = ""
        self.Loading = False
        self.ActiveItemHighlight = False
        self.ActiveSkillHighlight = False
        self.download_manager = DownloadManager(self)
        self.pdf_download_manager = PDFDownloadManager(self)
        
        #Add event filter to map, and two validators used for the text edits.
        self.MapGraphicsView.MapScene.installEventFilter(self)
        self.MapGraphicsView.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        
        self.regex_letters = QtCore.QRegularExpression("[a-zA-Z]+")
        self.validator_letters = QtGui.QRegularExpressionValidator(self.regex_letters, self)
        
        self.regex_numbers = QtCore.QRegularExpression("[0-9]+")
        self.validator_numbers = QtGui.QRegularExpressionValidator(self.regex_numbers, self)

        #Set line edits disabled colour, and add the validators and focus tracker.
        self.number_filter = NumberEditFilter()
        self.letter_filter = LetterEditFilter()
        for i in range(0,45):
            self.OrderEditsList[i].setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
            if i%3 == 0:
                self.OrderEditsList[i].setValidator(self.validator_letters)
                self.OrderEditsList[i].setMaxLength(1)
                self.OrderEditsList[i].setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.OrderEditsList[i].textChanged.connect(self.convert_to_upper)
                self.OrderEditsList[i].installEventFilter(self.letter_filter)
            else:
                self.OrderEditsList[i].setValidator(self.validator_numbers)
                self.OrderEditsList[i].installEventFilter(self.number_filter)
            self.OrderEditsList[i].textChanged.connect(self.render_movement)
        self.focus_tracker = FocusTracker(self)
        QtWidgets.QApplication.instance().installEventFilter(self.focus_tracker)

        #-----Set Icons-----
        for icon in self.EquipmentIconList:
            icon.setPixmap(self.blank_icon)
        for icon in self.BackpackIconList:
            icon.setPixmap(self.blank_icon)
        self.Character_Icon.setPixmap(self.blank_icon.scaled(64, 64))
        self.MadhouseLogo.setPixmap(self.madhouse_icon)
        self.HurstNetLogo.setPixmap(self.hurstnet_icon)
        self.MadhouseLogoMainMenu.setPixmap(self.madhouse_icon)
        self.HurstNetLogoMainMenu.setPixmap(self.hurstnet_icon)
        self.MadhouseBigLogo.setPixmap(self.madhouse_banner)
        self.DWTitle.setPixmap(self.DW_title)
        self.DWRogue.setPixmap(self.rogue_image)
        self.MadhouseBigLogo_2.setPixmap(self.madhouse_banner)
        self.DWMainImage.setPixmap(self.main_image)

        #Link banners to madhouse website
        self.link_filter = ClickableLinkFilter("www.madcentral.co.uk")
        self.MadhouseBigLogo.installEventFilter(self.link_filter)
        self.MadhouseBigLogo_2.installEventFilter(self.link_filter)

        #Link items + backpacks
        self.item_filter = ClickableItemFilter()
        for i in self.EquipmentIconList:
            i.installEventFilter(self.item_filter)
        for i in self.BackpackIconList:
            i.installEventFilter(self.item_filter)

        #Update turn num and download graphics, also check verification code.
        codeMismatch = True
        self.offline = False
        self.noPDFs = False
        try:
            #with open('Data/Account Verification.txt', 'r') as file:
                #data = file.readlines()[0].split(" - ")
                #self.AccountNum = data[0]
                #self.VerificationNum = data[1]
            data = load_encrypted_text('Data/Account Verification.txt', 'Data/Account Verification.dat', BaseKey).split(" - ")
            self.AccountNum = data[0]
            self.VerificationNum = data[1]
        except:
            pass

        try:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)

            sftp = paramiko.SFTPClient.from_transport(transport)

            with sftp.open(f"/VerificationCodes.txt", 'r') as remote_file:
                for line in remote_file:
                    try:
                        data = line.split(" - ")
                        if self.AccountNum == data[0] and self.VerificationNum == data[1].strip():
                            codeMismatch = False
                    except:
                        pass
        except: # Failed connection
            self.offline = True

        self.VerifiedPosNumbers = []
        self.NewPosNumbers = []

        if not codeMismatch:
            try:
                with open("Data/Server Turn Num.txt", 'r') as file: #Opens the old NVE file.
                    self.OldTurnNum = file.readlines()[0]
            except:
                self.offline = True
            try:
                with sftp.open(f"/ReportFile.txt", 'r') as remote_file:
                    for line in remote_file:
                        try:
                            data = line.split(",")
                            if data[1] in self.PosNumberDict and self.AccountNum == data[2]:
                                self.VerifiedPosNumbers.append(data[1])
                            elif self.AccountNum == data[2]:
                                self.NewPosNumbers.append(data[1])
                                self.VerifiedPosNumbers.append(data[1])
                        except:
                            pass
            except:
                pass

            try:
                self.pdf_dict = {}
                with sftp.open(f"/PDFs/Report.txt", 'rU') as remote_file:
                    Reportlines = remote_file.readlines()
                self.CorrectPDFPath = True
            except:
                try:
                    with sftp.open(f"/Report.txt", 'rU') as remote_file:
                        Reportlines = remote_file.readlines()
                    self.CorrectPDFPath = False
                except:
                    self.noPDFs = True

            if not self.noPDFs:
                cleaned_data = []
                for i in range(0,len(Reportlines)):
                    cleaned_data.append([])
                    for a in range(0,len(Reportlines[i].split('"'))):
                        if a%2 == 1:
                            cleaned_data[i].append(Reportlines[i].split('"')[a])
                counter = -2
                for i in cleaned_data:
                    if i[6] == "Postal":
                        pass
                    elif counter == -1 :
                        self.pdf_dict[i[0]] = ""
                        counter += 1
                    else:
                        self.pdf_dict[i[0]] = counter
                        counter += 1

            try:
                for i in range(1, 200):
                    try:
                        self.NewTurnNum = self.readPosNumber(sftp, f"/PrintFile{i}.nve")
                        with open('Data/Server Turn Num.txt', 'w') as file:
                            file.write(self.NewTurnNum)
                        break
                    except:
                        pass

                for i in self.NewPosNumbers: #Automatically add new positions
                    sftp.get(f"/PrintFile{i}.nve", f"Data/NVE Files/Player{i}.nve")
                    self.PosNumberDict[i] = self.NewTurnNum
                    self.AutoLoadDict[i] = []
                    self.LastSentDict[i] = "Not sent"
                    
                with open('Data/Position Numbers.txt', 'w') as file:
                    for key, value in self.PosNumberDict.items():
                        file.write(f"{key} - {value}\n")
                with open('Data/Last Sent.txt', 'w') as file:
                    for key, value in self.LastSentDict.items():
                        file.write(f"{key} - {value}\n")
                with open('Data/AutoLoad.txt', 'w') as file:
                    for key, value_list in self.AutoLoadDict.items():
                        self.formatted_string = f"{key} - {' '.join(value_list)}"
                        file.write(self.formatted_string + '\n')                    

                if self.OldTurnNum != self.NewTurnNum:
                    with open("Data/Graphics Check.txt", "r") as f:
                        check_date_str = f.read().strip()
                    check_date = datetime.strptime(check_date_str, "%d/%m/%y").date()
                    today_str = datetime.today().strftime("%d/%m/%y")
                    with open("Data/Graphics Check.txt", "w") as f:
                        f.write(today_str)
                    with sftp.open(f"/DateMod.txt", 'r') as remote_file:
                        for line_num, line in enumerate(remote_file, start=1):
                            line = line.strip()
                            if not line:
                                continue
                            date_str = line.split()[0]
                            remote_date = datetime.strptime(date_str, "%d/%m/%y").date()
                            if remote_date >= check_date:
                                remote_zip_path = f"/C32_{line_num}.zip"
                                local_zip_path = f"C32_{line_num}.zip"
                                local_bmp_path = f"Resources/Program Graphics/C32_{line_num}.bmp"

                                sftp.get(remote_zip_path, local_zip_path)

                                with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                                    bmp_inside_zip = f"Graphics/C32_{line_num}.bmp"
                                    zip_ref.extract(bmp_inside_zip, ".")
                                    shutil.move(bmp_inside_zip, local_bmp_path)

                                try:
                                    os.remove(local_zip_path)
                                    os.rmdir("Graphics")
                                except:
                                    pass
            except:
                self.offline = True

        try:
            sftp.close()
            transport.close()
        except:
            pass

        #Load main menu
        self.load_main_menu()

        #-----Change Program Properties-----
        if SettingsDict["theme"] == "Classic (Old NVE)": #Set background image, text colour, button background
            self.update_styleSheet("Resources/Program Graphics/backdrop.bmp", "#DEE3DE", "#CBD0CC")
            self.labelColour = "#DEE3DE"
            self.buttonColour = "#CBD0CC"
        elif SettingsDict["theme"] == "Papyrus":
            self.update_styleSheet("Resources/Program Graphics/papyrus.jpg", "#592824", "#CBD0CC")
            self.labelColour = "#DEE3DE"
            self.buttonColour = "#CBD0CC"
        elif SettingsDict["theme"] == "Windows Default":
            self.update_styleSheet("Default", "#1A1A1A", "#CBD0CC")
        elif SettingsDict["theme"] == "Slate":
            self.update_styleSheet("Resources/Program Graphics/stone.jpg", "#fbf7f5", "#CBD0CC")
        self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp")) #Change the program icon
        #self.showFullScreen()

        #Set buttons without functionality to red text
        self.UnimplementedButtons = []
        for i in self.UnimplementedButtons:
            i.setStyleSheet("""
                  QPushButton {
                      color: #A31D26;              /* Dark red text */
                  }
                  }
              """)

        sys.excepthook = except_hook #Replaces the standard exception handling with custom function

        #Prompt the user to update
        if updateAvailable:
            QtCore.QTimer.singleShot(10, show_update_popup)

        #Check verification code
        if codeMismatch and not self.offline:
            QtCore.QTimer.singleShot(10, show_verification_popup)

        if self.offline:
            QtCore.QTimer.singleShot(10, show_offline_popup)
            self.OfflineButtons = [self.DownloadPDFButton, self.DownloadNVEButton, self.SendOrdersButton]
            for i in self.OfflineButtons:
                i.setEnabled(False)
                i.setStyleSheet("""
                      QPushButton {
                          color: #A31D26;              /* Dark red text */
                      }
                      }
                  """)

        elif self.noPDFs:
            self.OfflineButtons = [self.DownloadPDFButton]
            for i in self.OfflineButtons:
                i.setEnabled(False)
                i.setStyleSheet("""
                      QPushButton {
                          color: #A31D26;              /* Dark red text */
                      }
                      }
                  """)

    def post_verify_Load(self):
        #with open('Data/Account Verification.txt', 'r') as file: #Run code from initial load we skipped if verification failed
            #data = file.readlines()[0].split(" - ")
            #self.AccountNum = data[0]
            #self.VerificationNum = data[1]
        data = load_encrypted_text('Data/Account Verification.txt', 'Data/Account Verification.dat', BaseKey).split(" - ")
        self.AccountNum = data[0]
        self.VerificationNum = data[1]
        
        transport = paramiko.Transport((hostname, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        self.VerifiedPosNumbers = []
        self.NewPosNumbers = []
        with open("Data/Server Turn Num.txt", 'r') as file: #Opens the old NVE file.
            self.OldTurnNum = file.readlines()[0]
        with sftp.open(f"/ReportFile.txt", 'r') as remote_file:
            for line in remote_file:
                try:
                    data = line.split(",")
                    if data[1] in self.PosNumberDict and self.AccountNum == data[2]:
                        self.VerifiedPosNumbers.append(data[1])
                    elif self.AccountNum == data[2]:
                        self.NewPosNumbers.append(data[1])
                        self.VerifiedPosNumbers.append(data[1])
                except:
                    pass
        for i in self.PosNumberDict:
            try:
                self.NewTurnNum = self.readPosNumber(sftp, f"/PrintFile{i}.nve")
                with open('Data/Server Turn Num.txt', 'w') as file:
                    file.write(self.NewTurnNum)
                break
            except:
                pass
        try: #Automatically add new positions
            for i in self.NewPosNumbers:
                sftp.get(f"/PrintFile{i}.nve", f"Data/NVE Files/Player{i}.nve")
                self.PosNumberDict[i] = self.NewTurnNum
                self.AutoLoadDict[i] = []
                self.LastSentDict[i] = "Not sent" 
        except:
            pass
        with open('Data/Position Numbers.txt', 'w') as file:
            for key, value in self.PosNumberDict.items():
                file.write(f"{key} - {value}\n")
        with open('Data/Last Sent.txt', 'w') as file:
            for key, value in self.LastSentDict.items():
                file.write(f"{key} - {value}\n")
        with open('Data/AutoLoad.txt', 'w') as file:
            for key, value_list in self.AutoLoadDict.items():
                self.formatted_string = f"{key} - {' '.join(value_list)}"
                file.write(self.formatted_string + '\n')             
        if self.OldTurnNum != self.NewTurnNum:
            with open("Data/Graphics Check.txt", "r") as f:
                check_date_str = f.read().strip()
            check_date = datetime.strptime(check_date_str, "%d/%m/%y").date()
            today_str = datetime.today().strftime("%d/%m/%y")
            with open("Data/Graphics Check.txt", "w") as f:
                f.write(today_str)
            with sftp.open(f"/DateMod.txt", 'r') as remote_file:
                for line_num, line in enumerate(remote_file, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    date_str = line.split()[0]
                    remote_date = datetime.strptime(date_str, "%d/%m/%y").date()
                    if remote_date >= check_date:
                        remote_zip_path = f"/C32_{line_num}.zip"
                        local_zip_path = f"C32_{line_num}.zip"
                        local_bmp_path = f"Resources/Program Graphics/C32_{line_num}.bmp"

                        sftp.get(remote_zip_path, local_zip_path)

                        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                            bmp_inside_zip = f"Graphics/C32_{line_num}.bmp"
                            zip_ref.extract(bmp_inside_zip, ".")
                            shutil.move(bmp_inside_zip, local_bmp_path)

                        try:
                            os.remove(local_zip_path)
                            os.remove("Graphics")
                        except:
                            pass

        sftp.close()
        transport.close()
        self.load_main_menu()

    def open_link(self):
        webbrowser.open(url)

    def centreMap(self):
        if self.PositionLoaded and self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
            tempZoom = self.MapGraphicsView._zoom + 3
            self.MapGraphicsView._zoom = -3
            factor = 0.8**tempZoom
            self.MapGraphicsView.scale(factor, factor)
            self.MapGraphicsView.centerOn((self.CurCharXPos)*self.MapGraphicsView.ZoomLevel-self.MapGraphicsView.ZoomLevel/2, (self.CurCharYPos)*self.MapGraphicsView.ZoomLevel-self.MapGraphicsView.ZoomLevel/2)

    def SelectLoad(self):
        match = re.search(r"\((\d+)\)$", self.CharactersCreatures_2.currentText())
        if match:
            if match.group(1) in self.CharactersList:
                self.LoadCharacter(match.group(1))
                index = self.CharactersList.index(match.group(1))
                self.CurCharIndex = index + 1
                return
        charType = self.CharactersCreatures_2.currentText().split(" - ")[0]
        if charType in list(window.saved_creature_data.keys()):
            self.open_creatureLibrary()
            index = self.itemCreatureWindow.CreaturesListBox.findText(self.CharactersCreatures_2.currentText().split(" - ")[0])
            if index != -1:
                self.itemCreatureWindow.CreaturesListBox.setCurrentIndex(index)

    def SelectItem(self):
        if self.Items.currentText().split(" - ", 1)[1] in list(window.saved_item_data.keys()):
            self.open_itemLibrary()
            index = self.itemLibraryWindow.ItemsListBox.findText(self.Items.currentText().split(" - ", 1)[1])
            if index != -1:
                self.itemLibraryWindow.ItemsListBox.setCurrentIndex(index)

    def MovePosUp(self):
        selected_item = self.positionList.currentItem()
        if selected_item:
            text = selected_item.text()
            match = re.search(r'Player (\d+)', text)
            if match:
                player_number = match.group(1)
                keys = list(self.PosNumberDict.keys())
                idx = keys.index(player_number)
                if idx != 0:
                    keys[idx - 1], keys[idx] = keys[idx], keys[idx - 1]
                    self.PosNumberDict = {k: self.PosNumberDict[k] for k in keys}
                    self.positionList.clear()
                    #Check to see if a new turn is available
                    self.NewTurnNum = ""
                    with open("Data/Server Turn Num.txt", 'r') as file: #Opens the old NVE file.
                        self.NewTurnNum = file.readlines()[0]
                    for i in self.PosNumberDict:
                        if i not in self.VerifiedPosNumbers:
                            self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: Position failed to verify")
                        elif self.NewTurnNum != self.PosNumberDict[i] and self.NewTurnNum != "":
                            self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: New turn available")
                        else:
                            self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: {self.LastSentDict[i]}")

                    with open('Data/Position Numbers.txt', 'w') as file:
                        for key, value in self.PosNumberDict.items():
                            file.write(f"{key} - {value}\n")
                    self.positionList.setCurrentRow(idx-1)

    def readPosNumber(self, sftp, remote_path):
        with sftp.open(remote_path, 'r') as remote_file:
            chars = []
            while True:
                c = remote_file.read(1).decode()
                if c == '^':
                    break
                chars.append(c)
            return ''.join(chars).strip()

    def MovePosDown(self):
        selected_item = self.positionList.currentItem()
        if selected_item:
            text = selected_item.text()
            match = re.search(r'Player (\d+)', text)
            if match:
                player_number = match.group(1)
                keys = list(self.PosNumberDict.keys())
                idx = keys.index(player_number)
                if idx != len(self.PosNumberDict)-1:
                    keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]
                    self.PosNumberDict = {k: self.PosNumberDict[k] for k in keys}
                    self.positionList.clear()
                    #Check to see if a new turn is available
                    self.NewTurnNum = ""
                    with open("Data/Server Turn Num.txt", 'r') as file: #Opens the old NVE file.
                        self.NewTurnNum = file.readlines()[0]
                    for i in self.PosNumberDict:
                        if i not in self.VerifiedPosNumbers:
                            self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: Position failed to verify")
                        elif self.NewTurnNum != self.PosNumberDict[i] and self.NewTurnNum != "":
                            self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: New turn available")
                        else:
                            self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: {self.LastSentDict[i]}")

                    with open('Data/Position Numbers.txt', 'w') as file:
                        for key, value in self.PosNumberDict.items():
                            file.write(f"{key} - {value}\n")
                    self.positionList.setCurrentRow(idx+1)

    def show_orderWindow(self, letter):
        self.letter = letter
        if hasattr(self, 'orderWindow') and self.orderWindow is not None:
            if self.orderWindow.isVisible():
                self.orderWindow.raise_()
                self.orderWindow.activateWindow()
                self.orderWindow.HeaderLabel.setText(f"Orders - {letter}")
                self.orderWindow.setWindowTitle(f"Orders - {letter}")
                file_path = f"Data/Information/Order Descriptions/{letter}.txt"
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.orderWindow.TextDisplay.setText(f.read())
                except FileNotFoundError:
                    self.orderWindow.TextDisplay.setText(f"File '{file_path}' not found.")
                return
            else:
                self.orderWindow.deleteLater()
                self.orderWindow = None
        self.orderWindow = OrderPopup() 
        self.orderWindow.show()
        self.orderWindow.setWindowTitle(f"Orders - {letter}")

    def load_main_menu(self):
        self.CurWindowSize = self.size()
        self.stackedWidget.setCurrentIndex(0)
        self.positionList.clear()
        self.setMaximumSize(QtCore.QSize(1900, 1080))
        #Check to see if a new turn is available
        with open("Data/Server Turn Num.txt", 'r') as file: #Opens the old NVE file.
            self.NewTurnNum = file.readlines()[0]
        for i in self.PosNumberDict:
            if self.offline:
                self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: Offline")
            elif i not in self.VerifiedPosNumbers:
                self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: Position failed to verify")
            elif self.NewTurnNum != self.PosNumberDict[i] and self.NewTurnNum != "":
                self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: New turn available")
            else:
                self.positionList.addItem(f"DungeonWorld Game 5 Player {i}: {self.LastSentDict[i]}")

    def main_load_position(self):
        selected_item = self.positionList.currentItem()
        if selected_item:
            text = selected_item.text()
            match = re.search(r'Player (\d+)', text)
            if match:
                player_number = match.group(1)
                new_test = text.split(": ")
                if new_test[1] == "New turn available":
                    show_new_turn_popup(player_number, selected_item)
                self.LoadPosition(player_number)
                self.stackedWidget.setCurrentIndex(1)
                self.setMaximumSize(QtCore.QSize(99999, 99999))
                self.resize(self.CurWindowSize)

    def main_download_pos(self):
        selected_item = self.positionList.currentItem()
        if selected_item:
            text = selected_item.text()
            new_test = text.split(": ")
            #if new_test[1] == "New turn available":
                # Extract player number using regex or string split
            match = re.search(r'Player (\d+)', text)
            if match and not self.offline:
                player_number = match.group(1)
                if player_number in self.VerifiedPosNumbers:
                    self.download_pos(player_number, selected_item)

    def main_download_pdf(self):
        selected_item = self.positionList.currentItem()
        if selected_item:
            text = selected_item.text()
            # Extract player number using regex or string split
            match = re.search(r'Player (\d+)', text)
            if match and not self.offline:
                player_number = match.group(1)
                if player_number in self.VerifiedPosNumbers:
                    self.download_pdf(player_number, selected_item)

    def download_pos(self, pos, selected_item):
        selected_item.setText(f"DungeonWorld Game 5 Player {pos}: NVE Queued for download")
        self.CloseNVEButton.setEnabled(False)
        self.ViewNVEButton.setEnabled(False)
        self.MoveUpButton.setEnabled(False)
        self.MoveDownButton.setEnabled(False)
        self.ViewNVEButton.setEnabled(False)
        self.DownloadPDFButton.setEnabled(False)
        self.ViewPDFButton.setEnabled(False)
        self.download_manager.add_download(pos, selected_item)

        return self.download_manager

    def download_pdf(self, pos, selected_item):
        selected_item.setText(f"DungeonWorld Game 5 Player {pos}: PDF Queued for download")
        self.CloseNVEButton.setEnabled(False)
        self.ViewNVEButton.setEnabled(False)
        self.MoveUpButton.setEnabled(False)
        self.MoveDownButton.setEnabled(False)
        self.ViewPDFButton.setEnabled(False)
        self.DownloadNVEButton.setEnabled(False)
        self.pdf_download_manager.add_download(pos, selected_item)

        return self.pdf_download_manager

    def view_pdf(self):
        try:
            selected_item = self.positionList.currentItem()
            if selected_item:
                text = selected_item.text()
                # Extract player number using regex or string split
                match = re.search(r'Player (\d+)', text)
                if match:
                    player_number = match.group(1)
                    os.startfile(f"Data\\PDFs\\Player{player_number}.pdf")
        except:
            pass
        
    def print_all_items(self):
        if self.PositionLoaded:
            for i in self.CharactersList:
                for slot in self.SlotList:
                    self.slotData = self.CharactersDict[i].DataDict[slot]
                    if self.slotData[0] != ' - Nothing Equipped' and self.slotData[0] !=  "- N/A":
                        print(self.slotData[0], i)
                for slot in self.BackpackList:
                    self.ItemName = self.CharactersDict[i].DataDict[slot][0]
                    if self.ItemName != "Empty" and self.ItemName != "Unusable" and self.ItemName != "Pint of Milk" and self.ItemName !=  "- N/A" and self.ItemName != "Bag Of Corn Seed":
                        print(self.ItemName, i)

    def print_all_skills(self):
        if self.PositionLoaded:
            for i in self.CharactersList:
                print(self.CharactersDict[i].DataDict["Other Details"])
                

    def write_message(self):
        if self.PositionLoaded:
            if hasattr(self, 'messageWindow') and self.messageWindow is not None:
                if self.messageWindow.isVisible():
                    self.messageWindow.raise_()
                    self.messageWindow.activateWindow()
                    return
                else:
                    self.messageWindow.deleteLater()
                    self.messageWindow = None
            self.messageWindow = WriteMessages() 
            self.messageWindow.show()
            self.messageWindow.setWindowTitle("Message Window")

    def view_messages(self):
        if self.PositionLoaded:
            if hasattr(self, 'VmessageWindow') and self.VmessageWindow is not None:
                if self.VmessageWindow.isVisible():
                    self.VmessageWindow.raise_()
                    self.VmessageWindow.activateWindow()
                    return
                else:
                    self.VmessageWindow.deleteLater()
                    self.VmessageWindow = None
            self.VmessageWindow = ViewMessages() 
            self.VmessageWindow.show()
            self.VmessageWindow.setWindowTitle("View Messages")

    def view_turn(self):
        if self.PositionLoaded:
            if self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
                if hasattr(self, 'turnWindow') and self.turnWindow is not None:
                    if self.turnWindow.isVisible():
                        self.turnWindow.raise_()
                        self.turnWindow.activateWindow()
                        return
                    else:
                        self.turnWindow.deleteLater()
                        self.turnWindow = None
                self.turnWindow = ViewTurn() 
                self.turnWindow.show()
                self.turnWindow.setWindowTitle("View Turn")

    def view_other_details(self):
        if self.PositionLoaded:
            if hasattr(self, 'detailsWindow') and self.detailsWindow is not None:
                if self.detailsWindow.isVisible():
                    self.detailsWindow.raise_()
                    self.detailsWindow.activateWindow()
                    return
                else:
                    self.detailsWindow.deleteLater()
                    self.detailsWindow = None
            self.detailsWindow = ViewOtherDetails() 
            self.detailsWindow.show()
            self.detailsWindow.setWindowTitle("Other Details")

    def open_settings(self):
        if hasattr(self, 'settingsWindow') and self.settingsWindow is not None:
            if self.settingsWindow.isVisible():
                self.settingsWindow.raise_()
                self.settingsWindow.activateWindow()
                return
            else:
                self.settingsWindow.deleteLater()
                self.settingsWindow = None
        self.settingsWindow = Settings() 
        self.settingsWindow.show()
        self.settingsWindow.setWindowTitle("Program Settings")

    def open_itemLibrary(self):
        if hasattr(self, 'itemLibraryWindow') and self.itemLibraryWindow is not None:
            if self.itemLibraryWindow.isVisible():
                self.itemLibraryWindow.raise_()
                self.itemLibraryWindow.activateWindow()
                return
            else:
                self.itemLibraryWindow.deleteLater()
                self.itemLibraryWindow = None
        self.itemLibraryWindow = ItemLibrary()
        self.item_focus_filter = ItemFocusFilter()
        self.itemLibraryWindow.installEventFilter(self.item_focus_filter)
        self.itemLibraryWindow.show()
        self.itemLibraryWindow.setWindowTitle("Items Library")

    def open_skillLibrary(self):
        if hasattr(self, 'skillLibraryWindow') and self.skillLibraryWindow is not None:
            if self.skillLibraryWindow.isVisible():
                self.skillLibraryWindow.raise_()
                self.skillLibraryWindow.activateWindow()
                return
            else:
                self.skillLibraryWindow.deleteLater()
                self.skillLibraryWindow = None
        self.skillLibraryWindow = SkillLibrary()
        self.skill_focus_filter = SkillFocusFilter()
        self.skillLibraryWindow.installEventFilter(self.skill_focus_filter)
        self.skillLibraryWindow.show()
        self.skillLibraryWindow.setWindowTitle("Skills Library")

    def open_creatureLibrary(self):
        if hasattr(self, 'itemCreatureWindow') and self.itemCreatureWindow is not None:
            if self.itemCreatureWindow.isVisible():
                self.itemCreatureWindow.raise_()
                self.itemCreatureWindow.activateWindow()
                return
            else:
                self.itemCreatureWindow.deleteLater()
                self.itemCreatureWindow = None
        self.itemCreatureWindow = CreatureLibrary()
        self.itemCreatureWindow.show()
        self.itemCreatureWindow.setWindowTitle("Creatures Library")

    def convert_to_upper(self, text):
        """Convert entered text to upper case and focus next text edit."""
        sender = self.sender()
        if text.isalpha():
            sender.blockSignals(True)
            sender.setText(text.upper())
            sender.blockSignals(False)
            self.focusNextChild()

    def update_styleSheet(self, image_path, text_colour, button_colour): #Function for updating anything style sheet related, currently used for background image and text colour
        if image_path == "Default":
            self.setStyleSheet("")
            self.positionList.setStyleSheet("""
                QListWidget::item:selected {
                    background-color: lightgreen;
                    color: black;
                }
            """)
            font = QtGui.QFont("MS Shell Dlg 2", 10, QtGui.QFont.Weight.Bold)
            self.positionList.setFont(font)
            for orderEdit in self.OrderEditsList:
                orderEdit.setStyleSheet("QLineEdit { padding: 1px; } QLineEdit:disabled { background-color: #727272; color: black; }")
            for button in self.findChildren(QtWidgets.QPushButton):
                button.setStyleSheet(f"")

            for widget in self.findChildren(QtWidgets.QComboBox):
                widget.setStyleSheet(f"")

        else:
            current_stylesheet = self.styleSheet() #Retrieve the current stylesheet

            # Add the new settings to the stylesheet
            new_stylesheet = f"""
            {current_stylesheet}
            QLabel {{
                color: {text_colour};
            }}
            QCheckBox {{
                color: {text_colour};
            }}

            QMainWindow {{
                background-image: url({image_path});
                background-position: center;
            }}
            QToolTip {{
                max-width: 600px;
                white-space: pre;
                background-color: #ffffe0;
                color: #black;
                border: 1px solid black;
            }}
            """

            self.positionList.setStyleSheet("""
                QListWidget{
                    background-color: white;
                }
                
                QListWidget::item {
                    color: black;
                    background-color: white;
                }

                QListWidget::item:selected {
                    background-color: lightgreen;
                    color: black;
                }
            """)
            font = QtGui.QFont("MS Shell Dlg 2", 10, QtGui.QFont.Weight.Bold)
            self.positionList.setFont(font)

            for orderEdit in self.OrderEditsList:
                orderEdit.setStyleSheet("QLineEdit { padding: 1px; background-color: #CBD0CC; color: black;} QLineEdit:disabled { background-color: #727272; color: black; }")
##                orderEdit.setStyleSheet("""
##                    QLineEdit:enabled {
##                        background-color: #CBD0CC;
##                        color: black;
##                        margin: 0px;
##                    }
##                    QLineEdit:disabled {
##                        background-color: #727272;
##                        color: black;
##                        margin: 0px;
##                    }
##                """)

            for button in self.findChildren(QtWidgets.QPushButton):
                button.setStyleSheet(f"background-color: {button_colour}; color: black; ")

            for widget in self.findChildren(QtWidgets.QComboBox):
                widget.setStyleSheet(f"background-color: {button_colour}; color: black; ")
          
            self.setStyleSheet(new_stylesheet) #Apply the new stylesheet

    def EraseOrder(self):
        try:
            self.focused_Order = int(self.OrderEditsList.index(self.focus_tracker.last_focused_widget)/3)
            for i in range(0, 3):
                self.OrderEditsList[self.focused_Order*3+i].blockSignals(True)
                self.OrderEditsList[self.focused_Order*3+i].setText("")
                self.OrderEditsList[self.focused_Order*3+i].blockSignals(False)
            if self.focused_Order == 0:
                self.OrderEditsList[0].setFocus()
            elif self.OrderEditsList[self.focused_Order*3-1].text() == "" and self.OrderEditsList[self.focused_Order*3-2].text() == "":
                self.OrderEditsList[self.focused_Order*3-3].setFocus()
            elif self.OrderEditsList[self.focused_Order*3-1].text() == "":
                self.OrderEditsList[self.focused_Order*3-2].setFocus()
            else:
                self.OrderEditsList[self.focused_Order*3-1].setFocus()
            self.render_movement()
        except:
            pass

    def EraseMoveUp(self):
        try:
            self.focused_Order = int(self.OrderEditsList.index(self.focus_tracker.last_focused_widget)/3)
            for i in range(self.focused_Order, 14):
                for j in range(0,3):
                    self.OrderEditsList[i*3+j].blockSignals(True)
                    self.OrderEditsList[i*3+j].setText(self.OrderEditsList[i*3+j+3].text())
                    self.OrderEditsList[i*3+j].blockSignals(False)
            for i in range(0,3):
                self.OrderEditsList[42+i].blockSignals(True)
                self.OrderEditsList[42+i].setText("")
                self.OrderEditsList[42+i].blockSignals(False)
            for i in range(0,3):
                if i == 2:
                    self.OrderEditsList[self.focused_Order*3+2-i].setFocus()
                elif self.OrderEditsList[self.focused_Order*3+2-i].text() != "":
                    self.OrderEditsList[self.focused_Order*3+2-i].setFocus()
                    break
            self.render_movement()
        except:
            pass

    def CopyToEnd(self): 
        try:
            self.focused_Order = int(self.OrderEditsList.index(self.focus_tracker.last_focused_widget)/3)
            for i in range(self.focused_Order+1,int(self.CharactersDict[self.CurLoadedChar].DataDict["NumOrders"])):
                for j in range(0,3):
                    self.OrderEditsList[i*3+j].blockSignals(True)
                    self.OrderEditsList[i*3+j].setText(self.OrderEditsList[self.focused_Order*3+j].text())
                    self.OrderEditsList[i*3+j].blockSignals(False)
            self.OrderEditsList[int(self.CharactersDict[self.CurLoadedChar].DataDict["NumOrders"])*3-1].setFocus()
            self.render_movement()
        except:
            pass

    def EraseAll(self):
        try:
            for i in self.OrderEditsList:
                i.blockSignals(True)
                i.setText("")
                i.blockSignals(False)
            self.OrderEditsList[0].setFocus()
            self.render_movement()
        except:
            pass

    def MoveAllDown(self):
        totalOrders = int(self.CharactersDict[self.CurLoadedChar].DataDict["NumOrders"])
        self.focused_Order = int(self.OrderEditsList.index(self.focus_tracker.last_focused_widget)/3)
        try:
            self.FocusSet = False
            for i in range(totalOrders * 3 - 1, self.focused_Order * 3 - 1, -1):
                if i > self.focused_Order * 3 + 2:
                    self.OrderEditsList[i].blockSignals(True)
                    self.OrderEditsList[i].setText(self.OrderEditsList[i-3].text())
                    self.OrderEditsList[i].blockSignals(False)
                else:
                    self.OrderEditsList[i].blockSignals(True)
                    self.OrderEditsList[i].setText("")
                    self.OrderEditsList[i].blockSignals(False)
                    self.OrderEditsList[self.focused_Order*3].setFocus()
            self.render_movement()
        except:
            pass

    def CopyCurrentDown(self):
        try:
            self.focused_Order = int(self.OrderEditsList.index(self.focus_tracker.last_focused_widget)/3)
            if self.focused_Order > 0:
                for i in range(0, 3):
                    self.OrderEditsList[self.focused_Order*3+i].blockSignals(True)
                    self.OrderEditsList[self.focused_Order*3+i].setText(self.OrderEditsList[self.focused_Order*3+i-3].text())
                    self.OrderEditsList[self.focused_Order*3+i].blockSignals(False)
                if self.focused_Order < 14:
                    for i in range(0,3):
                        if i == 2:
                            self.OrderEditsList[self.focused_Order*3+5-i].setFocus()
                        elif self.OrderEditsList[self.focused_Order*3+5-i].text() != "":
                            self.OrderEditsList[self.focused_Order*3+5-i].setFocus()
                            break
                else:
                    for i in range(0,3):
                        if i == 2:
                            self.OrderEditsList[44-i].setFocus()
                        elif self.OrderEditsList[44-i].text() != "":
                            self.OrderEditsList[44-i].setFocus()
                            break
            self.render_movement()
        except:
            pass
        

    def BuildOrders(self):
        if self.PositionLoaded and self.CurLoadedPos in self.VerifiedPosNumbers:
            self.SaveOrders()
            
            self.writeString = f"#g{self.GameNum} #p{self.CurLoadedPos} #a{self.AccountNum}" #Start of string
            
            for character in sorted(self.CharactersList, key=int): #Loop each character
                self.writeString = self.writeString + f" #c{character}" #Add character number
                try: #Add orders
                    self.OrdersFile = open(f"Data/Current Orders/{character}", 'rb')
                    self.OrdersString = self.OrdersFile.read().hex()
                    self.OrdersFile.close()
                    self.OrdersString = [self.OrdersString[i:i+8] for i in range(0, len(self.OrdersString), 8)]
                    for i in range(0,len(self.OrdersString)):
                        if i%3 == 0:
                            self.OrdersString[i] = chr(int(self.OrdersString[i][0:2], 16))
                        else:
                            self.OrdersString[i] = sum(int(self.OrdersString[i][j*2:(j+1)*2], 16)*256**j for j in range(4))
                    for i in range(0,15):
                        if self.OrdersString[i*3] != '\x00':
                            self.writeString = self.writeString + f" &{i+1} {self.OrdersString[i*3]} {str(self.OrdersString[i*3+1])} {str(self.OrdersString[i*3+2])}"
                except: #No orders for that character
                    pass

            try: #Add message
                with open(f"Data/Messages/DungeonWorld5-{self.CurLoadedPos}dun-msg", 'rb') as f:
                    self.strings = []
                    while True:
                        length_bytes = f.read(2)
                        if not length_bytes:
                            break
                        length = int.from_bytes(length_bytes, byteorder='little')
                        string_bytes = f.read(length)
                        string_data = string_bytes[:-1].decode('ascii')
                        self.strings.append(string_data)
                    for i in range(0, 4):
                        self.strings[i] = self.strings[i] + " "
                    self.writeString = self.writeString + f' #message"{self.strings[0]}""{self.strings[1]}""{self.strings[2]}""{self.strings[3]}"'
            except: #No message
                self.writeString = self.writeString + " #message"

            self.writeString = self.writeString + "#EOF" #EOF

            self.path = f'Data/DUN Files/G{self.GameNum}P{self.CurLoadedPos}.dun'
            with open(self.path, 'w') as file: #Write to file
                file.write(self.writeString)

            local_path = f'Data/DUN Files/G{self.GameNum}P{self.CurLoadedPos}.dun'

            if not os.path.exists(local_path):
                self.message = f"Upload failed: local file not found ({local_path})"
            else:
                try:
                    transport = paramiko.Transport((hostname, port))
                    transport.connect(username=username, password=password)
                    sftp = paramiko.SFTPClient.from_transport(transport)
                    try:
                        sftp.put(local_path, f"/DUNfiles/G{self.GameNum}P{self.CurLoadedPos}.dun")
                        self.current_time = QtCore.QDateTime.currentDateTime().toString("dddd MMMM dd hh:mm")
                        self.message = f"Your orders were received and have been uploaded to the server on:\n{self.current_time}"
                        self.LastSentDict[self.CurLoadedPos] = self.current_time
                        with open('Data/Last Sent.txt', 'w') as file:
                            for key, value in self.LastSentDict.items():
                                file.write(f"{key} - {value}\n")
                        self.OrdersLastSentLabel.setText(f"{self.LastSentDict[self.CurLoadedPos]}")
                        self.OrdersLastSentLabel.setStyleSheet("")
                    except Exception as upload_error:
                        self.message = f"Upload failed: {upload_error}"
                    sftp.close()
                    transport.close()
                except Exception as conn_error:
                    self.message = f"Upload failed: Failed to connect to SFTP server ({conn_error})"

            if "Upload failed" not in self.message:
                self.ReceivedDialog = MessageDialog(self.message, "Orders Received", self)
            else:
                self.ReceivedDialog = MessageDialog(self.message, "Upload failed", self)
            self.ReceivedDialog.exec()


    def LoadAllLast(self):
        if self.PositionLoaded:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle("Please confirm")
            msg_box.setText("This will load ALL character's last orders, overwriting any current orders. Are you sure you want to continue?")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            msg_box.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp"))

            reply = msg_box.exec()
            
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                for i in self.CharactersList:
                    try:
                        shutil.copy("Data/Last Orders/" + i, "Data/Current Orders/" + i) #self.setWindowIcon(QtGui.QIcon("Resources/Program Graphics/logo1.bmp"))
                    except:
                        pass
                self.LoadOrders("Data/Current Orders/" + self.CurLoadedChar)

    def LoadCurLast(self):
        if self.PositionLoaded:
            try:
                shutil.copy("Data/Last Orders/" + self.CurLoadedChar, "Data/Current Orders/" + self.CurLoadedChar)
            except:
                pass
            self.LoadOrders("Data/Current Orders/" + self.CurLoadedChar)

    def AskPosition(self): #Function for the user to choose a position to swap to
        if self.PositionLoaded:
            self.SaveOrders()
        self.PositionDialog = ChoosePositionDialog(self) #Creates the popup dialog so the user can select a position
        if self.PositionDialog.exec(): #True if the dialog is accepted, gets the selected position number and runs the function to load the position
            self.selected_PosNumber = str(self.PositionDialog.get_selected_number())
            #Check to see if a new turn is available
            self.NewTurnNum = ""
            with open("Data/Server Turn Num.txt", 'r') as file: #Opens the old NVE file.
                self.NewTurnNum = file.readlines()[0]

            if self.NewTurnNum != self.PosNumberDict[self.selected_PosNumber] and self.NewTurnNum != "":
                show_new_turn_popup(self.selected_PosNumber)
            self.LoadPosition(self.selected_PosNumber)

    def UpdateAutoLast(self): 
        if self.PositionLoaded and not self.UpdatingCheckbox:
            if self.AutoLoadLastOrders.isChecked():
                self.AutoLoadDict[self.CurLoadedPos].append(self.CurLoadedChar)
            else:
                self.AutoLoadDict[self.CurLoadedPos].remove(self.CurLoadedChar)
            with open('Data/AutoLoad.txt', 'w') as file:
                for key, value_list in self.AutoLoadDict.items():
                    self.formatted_string = f"{key} - {' '.join(value_list)}"
                    file.write(self.formatted_string + '\n')

    def LoadPosition(self, PosNumber):
        self.Loading = True
        self.CurLoadedPos = PosNumber
        self.setEnabled(False)
        
        self.progress_popup = ProgressPopup()
        self.progress_popup.show()

        self.thread = QtCore.QThread()
        self.loader = PositionLoader(PosNumber, self)

        self.loader.moveToThread(self.thread)

        self.loader.progress_updated.connect(self.progress_popup.update_progress)
        self.loader.label_updated.connect(self.progress_popup.update_label)
        self.loader.finished.connect(self.thread.quit)
        self.loader.finished.connect(self.loader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.loader.finished.connect(self.progress_popup.close)

        self.loader.finished.connect(lambda: self.setEnabled(True))

        self.loader.finished.connect(self.loading_finished)

        self.thread.started.connect(self.loader.run)
        self.thread.start()

    def loading_finished(self):
        if SettingsDict["Use Custom Class Ordering"] == "True":
            tempcharList = self.CharactersList.copy()
            self.CharactersList = []
            for ClassName in self.ClassOrder:
                for CharNum in tempcharList:
                    if self.CharactersDict[CharNum].DataDict["Class"] == ClassName:
                        self.CharactersList.append(CharNum)
        
        self.WriteMaps() 
        self.LoadCharacter(self.CharactersList[0])
        self.CurCharIndex = 1
        self.PositionLoaded = True
        self.PosData = []
        self.OrdersLastSentLabel.setText(f"{self.LastSentDict[self.CurLoadedPos]}")
        if self.LastSentDict[self.CurLoadedPos] == "Not sent":
            self.OrdersLastSentLabel.setStyleSheet("color: #D40000;")
        else:
            self.OrdersLastSentLabel.setStyleSheet("")
        self.Loading = False

    def copy_files(self, src_dir, dst_dir):
        # Ensure the destination directory exists
        os.makedirs(dst_dir, exist_ok=True)
        
        # List all files in the source directory
        for filename in os.listdir(src_dir):
            # Construct full file paths
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join(dst_dir, filename)
            
            # Copy only files (ignore directories)
            if os.path.isfile(src_file):
                shutil.copy(src_file, dst_file)

    def FindCharacter(self):
        if self.PositionLoaded:
            self.findCharDialog = FindCharacterDialog(self.CharactersList, self.CurLoadedPos, self.FindCharacterLoad, self)
            self.findCharDialog.exec()

    def FindCharacterLoad(self, number, index):
        self.CurCharIndex = index + 1
        self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])

    def SaveOrders(self):
        self.CurOrders = []
        self.Counter = 0
        self.EmptyCount = 0
        while self.Counter < 45:
            if self.OrderEditsList[self.Counter].text() == "" and self.Counter%3 == 0:
                self.EmptyCount += 1
                self.CurOrders.append("0")
                self.CurOrders.append("0")
                self.CurOrders.append("0")
                self.Counter += 3
            elif self.OrderEditsList[self.Counter].text() == "":
                self.CurOrders.append("0")
                self.Counter += 1
            else:
                self.CurOrders.append(self.OrderEditsList[self.Counter].text())
                self.Counter += 1

        if self.EmptyCount == 15:
            try:
                os.remove("Data/Current Orders/" + self.CurLoadedChar)
            except:
                pass
        else:
            self.bytesString = b'' #Store contents of file
            for i in range(0,15):
                if self.CurOrders[i*3] == "0":
                    self.bytesString = self.bytesString + chr(0).encode('latin1') + (''.join(chr(205) for j in range(3))).encode('latin1') + (''.join(chr(0) for k in range(8))).encode('latin1')
                else:
                    self.bytesString = self.bytesString + self.CurOrders[i*3].encode('latin1') + (''.join(chr(205) for j in range(3))).encode('latin1') + self.num_to_bytes(int(self.CurOrders[i*3+1])) + self.num_to_bytes(int(self.CurOrders[i*3+2]))
            
            self.File = open("Data/Current Orders/" + self.CurLoadedChar,"wb") #Save bytes data in binary file 
            self.File.write(self.bytesString)
            self.File.close()

    def LoadOrders(self, file):
        try:
            self.OrdersFile = open(file, 'rb')
            self.OrdersString = self.OrdersFile.read().hex()
            self.OrdersFile.close()
            self.OrdersString = [self.OrdersString[i:i+8] for i in range(0, len(self.OrdersString), 8)]
            for i in range(0,len(self.OrdersString)):
                if i%3 == 0:
                    self.OrdersString[i] = chr(int(self.OrdersString[i][0:2], 16))
                else:
                    self.OrdersString[i] = sum(int(self.OrdersString[i][j*2:(j+1)*2], 16)*256**j for j in range(4))
            for i in range(0,45):
                self.CurString = str(self.OrdersString[i])
                if self.CurString != '\x00' and self.CurString != '0':
                    self.OrderEditsList[i].blockSignals(True)
                    self.OrderEditsList[i].setText(str(self.OrdersString[i]))
                    self.OrderEditsList[i].blockSignals(False)
                else:
                    self.OrderEditsList[i].blockSignals(True)
                    self.OrderEditsList[i].setText("")
                    self.OrderEditsList[i].blockSignals(False)
        except:
            for i in self.OrderEditsList:
                i.blockSignals(True)
                i.setText("")
                i.blockSignals(False)
        self.render_movement()

    def render_movement(self):
        if self.CurLoadedMap != "None":
            self.MoveList = []
            for i in range(0,15):
                if self.OrderEditsList[i*3].text() == "M":
                    self.MoveList.append(self.OrderEditsList[i*3+1].text())
            self.CurCharXPos = int(float(self.CharactersDict[self.CurLoadedChar].DataDict["XPos"]))
            self.CurCharYPos = int(float(self.CharactersDict[self.CurLoadedChar].DataDict["YPos"]))
            self.moveCost = 0
            self.tempXPos = self.CurCharXPos - 1
            self.tempYPos = self.CurCharYPos - 1
            self.move_deltas = [(0, 0), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
            for i in self.MoveList:
                if i != "":
                    self.moveNum = int(i)
                    if self.moveNum > 0 and self.moveNum < 9:
                        dx, dy = self.move_deltas[self.moveNum]
                        self.tempXPos += dx
                        self.tempYPos += dy
                        try:
                            self.key = self.MapsDict[self.CurLoadedMap].DataList[(int(self.tempXPos)+int(self.tempYPos)*int(self.MapsDict[self.CurLoadedMap].DataList[0]))*5+2]
                            if self.key != "0.0":
                                self.curMoveData = self.TerrainKeys[self.key].split("^")[3].split()[1]
                            else:
                                self.curMoveData = 0
                            try:
                                self.moveCost += int(self.curMoveData)
                            except:
                                pass
                        except:
                            pass
            if self.moveCost > 0:
                self.MoveRateValue.setText(f"{self.CharactersDict[self.CurLoadedChar].DataDict['Move Rate']} - {str(self.moveCost)}")
                if self.moveCost > int(self.CharactersDict[self.CurLoadedChar].DataDict['Move Rate']):
                    self.MoveRateValue.setStyleSheet("color: #D40000;")
                else:
                    self.MoveRateValue.setStyleSheet("")
            else:
                self.MoveRateValue.setStyleSheet("")
            self.MapGraphicsView.drawMovement(self.MoveList, self.CurCharXPos, self.CurCharYPos)
    
    def num_to_bytes(self, number): #Converts number for column of order to bytes form
        returnBytes = b''
        byteList = []
        for i in reversed(range(4)): #Calculate each place value of number in base 256 starting from left (more efficient as reduces calculations)
            byteList.append(chr(number // (256**i)).encode('latin1')) 
            number = number % (256**i)   
        for i in reversed(range(4)): #...but then add backwards because the NVE reads right to left?
            returnBytes = returnBytes + byteList[i]
        return returnBytes

    def WriteMaps(self): #Function to write maps from dictionary to map files
        for i in self.MapsDict:
            self.WriteStr = '^'.join(self.MapsDict[i].DataList)
            #with open('Data/Maps/'+i, 'w') as file:
                #file.write(self.WriteStr)
            save_encrypted_text(self.WriteStr, f'Data/Maps/{i}.dat', EncKey)

    def LoadCharacter(self, Num): #Num should be string
        if self.PositionLoaded:
            self.SaveOrders()
            
        #----------------------------Todo: Shop equipment and stats----------------------------------------------
        if self.CharactersDict[Num].DataDict["CharCost"].split()[0] == "Castle":
            self.HealthLabel.setText("State of Repair")
            self.LastAteLabel.setText("Last Inventory:")
            self.LastSleptLabel.setText("Last Festival:")
            self.EquipmentLabel.setText("Active Staff")
            self.BackpackLabel.setText("Standby Staff")
            self.DamageLabel.setText("Defensive Potential")
            for index, (var, slot) in enumerate(zip(self.EquipmentHeadersList, self.StaffList), start=1):
                var.setText(f"[{index}] {slot}")
        elif self.CharactersDict[Num].DataDict["CharCost"].split()[0] == "Character":
            self.HealthLabel.setText("Health")
            self.LastAteLabel.setText("Last Ate: ")
            self.LastSleptLabel.setText("Last Slept:")
            self.EquipmentLabel.setText("Equipment")
            self.BackpackLabel.setText("Backpack")
            self.DamageLabel.setText("Damage")
            for index, (var, slot) in enumerate(zip(self.EquipmentHeadersList, self.CharactersDict[Num].DataDict["Equipment Names"]), start=1):
                var.setText(f"[{index}] {slot}")
        
        self.CurLoadedChar = self.CharactersDict[Num].DataDict["Number"]

        self.CharGraphicList = self.CharactersDict[Num].DataDict["CharGraphic"]
        self.Character_Icon.setPixmap(self.GetPixmap(self.CharGraphicList[0],self.CharGraphicList[1],64))
        self.CharacterNameLabelandIDValue.setText(self.CharactersDict[Num].DataDict["Name"] + " (" + self.CurLoadedChar + ")")
        self.CharacterClassValue.setText(self.CharactersDict[Num].DataDict["Class"])
        self.CurHP = self.CharactersDict[Num].DataDict["HP"].split()[-4]
        self.MaxHP = self.CharactersDict[Num].DataDict["HP"].split()[-1]
        self.HealthValue.setText(self.CurHP + "/" + self.MaxHP)
        if int(self.CurHP) <= int(self.MaxHP) * int(SettingsDict["Red Health"]) / 100:
            self.HealthValue.setStyleSheet("color: #D40000;")
        elif int(self.CurHP) <= int(self.MaxHP) * int(SettingsDict["Amber Health"]) / 100:
            self.HealthValue.setStyleSheet("color: #FFBF00;")
        else:
            self.HealthValue.setStyleSheet("")
        self.ExperienceValue.setText(self.CharactersDict[Num].DataDict["Experience"])
        self.GoldValue.setText(self.CharactersDict[Num].DataDict["Gold"])
        self.CurLastAte = self.CharactersDict[Num].DataDict["Last Ate"]
        self.LastAteValueLabel.setText(self.CurLastAte)
        try:
            if int(self.CurLastAte) >= int(SettingsDict["Red Ate"]):
                self.LastAteValueLabel.setStyleSheet("color: #D40000;")
            elif int(self.CurLastAte) >= int(SettingsDict["Amber Ate"]):
                self.LastAteValueLabel.setStyleSheet("color: #FFBF00;")
            else:
                self.LastAteValueLabel.setStyleSheet("")
        except:
            self.LastAteValueLabel.setStyleSheet("")
        self.CurLastSlept = self.CharactersDict[Num].DataDict["Last Slept"]
        self.LastSleptValueLabel.setText(self.CurLastSlept)
        try:
            if int(self.CurLastSlept) >= int(SettingsDict["Red Slept"]):
                self.LastSleptValueLabel.setStyleSheet("color: #D40000;")
            elif int(self.CurLastSlept) >= int(SettingsDict["Amber Slept"]):
                self.LastSleptValueLabel.setStyleSheet("color: #FFBF00;")
            else:
                self.LastSleptValueLabel.setStyleSheet("")
        except:
            self.LastAteValueLabel.setStyleSheet("")
        if len(self.CharactersDict[Num].DataDict["Alignment"].split()) > 1:
            self.AlignmentValueLabel.setText(self.CharactersDict[Num].DataDict["Alignment"].split()[1])
        else:
            self.AlignmentValueLabel.setText(self.CharactersDict[Num].DataDict["Alignment"].removeprefix("Alignment").lstrip())
        self.HostilityValueLabel.setText(self.CharactersDict[Num].DataDict["Hostility"])
        self.AggressionValueLabel.setText(self.CharactersDict[Num].DataDict["Aggression"])
        self.FearFactorValueLabel.setText(self.CharactersDict[Num].DataDict["Fear Factor"])
        if self.CharactersDict[Num].DataDict["CharCost"].split()[0] != "Shop":
            for var, slot in zip(self.EquipmentLabelsList, self.SlotList):
                var.setText(self.CharactersDict[Num].DataDict[slot][0])
            for icon, slot, label in zip(self.EquipmentIconList, self.SlotList, self.EquipmentHeadersList):
                self.slotData = self.CharactersDict[Num].DataDict[slot]
                self.descData = self.saved_item_data.get(self.slotData[0], {}).get("description_1", "")
                self.desc_html = f'<p style="margin:0; white-space: pre-wrap;">{self.descData}</p>' if self.descData else ''
                self.noteData = self.saved_item_data.get(self.slotData[0], {}).get("description_2", "")
                self.note_html = f'<p style="margin:0; white-space: pre-wrap;">Player notes: {self.noteData}</p>' if self.noteData else ''
                if len(self.slotData) > 4:
                    icon.setPixmap(self.GetPixmap(self.slotData[1],self.slotData[2],32))
                    icon.setToolTip(f"""
                    <html>
                      <body>
                        <p style="margin:0;">{label.text().split(' ', 1)[1] if ' ' in label.text() else ''}</p>
                        <p style="margin:0; white-space: nowrap;">{self.slotData[0]}</p>
                        <p style="margin:0; white-space: nowrap;">Attack: {self.slotData[5]}</p>
                        <p style="margin:0; white-space: nowrap;">Damage: {self.slotData[6]}-{self.slotData[7]} ({self.slotData[4]})</p>
                        {self.desc_html}
                        {self.note_html}
                      </body>
                    </html>
                    """)
                elif len(self.slotData) > 1:
                    icon.setPixmap(self.GetPixmap(self.slotData[1],self.slotData[2],32))
                    icon.setToolTip(f"""
                    <html>
                      <body>
                        <p style="margin:0;">{label.text().split(' ', 1)[1] if ' ' in label.text() else ''}</p>
                        <p style="margin:0; white-space: nowrap;">{self.slotData[0]}</p>
                        {self.desc_html}
                        {self.note_html}
                      </body>
                    </html>
                    """)
                else:
                    icon.setPixmap(self.blank_icon)
                    icon.setToolTip(f"""
                    <html>
                      <body>
                        <p style="margin:0;">{label.text().split(' ', 1)[1] if ' ' in label.text() else ''}</p>
                        <p style="margin:0; white-space: nowrap;">{self.slotData[0]}</p>
                        {self.desc_html}
                        {self.note_html}
                      </body>
                    </html>
                    """)
            for label, value, stat in zip(self.StatLabelList, self.StatValueList, self.CharactersDict[Num].DataDict["Statistics"]):
                label.setText(stat.split(': ')[0])
                value.setText(stat.split(': ')[1].strip())
            self.Counter = 1
            for label, quantity, slot in zip(self.BackpackLabelsList, self.BackpackQuantityList, self.BackpackList):
                self.ItemName = self.CharactersDict[Num].DataDict[slot][0]
                label.setText(self.ItemName)
                if self.ItemName != "Empty" and self.ItemName != "Unusable":
                    quantity.setText(f"[{self.Counter}] x {self.CharactersDict[Num].DataDict[slot][4]}")
                else:
                    quantity.setText(f"[{self.Counter}]")
                self.Counter += 1
            for icon, slot in zip(self.BackpackIconList, self.BackpackList):
                self.slotData = self.CharactersDict[Num].DataDict[slot]
                self.descData = self.saved_item_data.get(self.slotData[0], {}).get("description_1", "")
                self.desc_html = f'<p style="margin:0; white-space: pre-wrap;">{self.descData}</p>' if self.descData else ''
                self.noteData = self.saved_item_data.get(self.slotData[0], {}).get("description_2", "")
                self.note_html = f'<p style="margin:0; white-space: pre-wrap;">Player notes: {self.noteData}</p>' if self.noteData else ''
                if len(self.slotData) > 1:
                    icon.setPixmap(self.GetPixmap(self.slotData[1],self.slotData[2],32))
                    icon.setToolTip(f"""
                    <html>
                      <body>
                        <p style="margin:0;">Equip to: {self.slotData[5]}</p>
                        <p style="margin:0; white-space: nowrap;">{self.slotData[0]}</p>
                        {self.desc_html}
                        {self.note_html}
                      </body>
                    </html>
                    """)
                else:
                    icon.setPixmap(self.blank_icon)
                    icon.setToolTip(f"Empty")
        self.VisionValue.setText(self.CharactersDict[Num].DataDict["Vision"])
        self.MoveRateValue.setText(self.CharactersDict[Num].DataDict["Move Rate"])
        self.AttackValue.setText(self.CharactersDict[Num].DataDict["Attack"])
        self.DamageValue.setText(self.CharactersDict[Num].DataDict["Damage"].split(": ")[1][:-2])
        for label, defence, dr in zip(self.DefenceLabelList, self.CharactersDict[Num].DataDict["Defences"], self.CharactersDict[Num].DataDict["DamRed"]):
            label.setText(defence + " / " + dr)
        for i in range(0,int(self.CharactersDict[Num].DataDict["NumOrders"])):
            self.OrderEditsList[i*3].setDisabled(False)
            self.OrderEditsList[i*3+1].setDisabled(False)
            self.OrderEditsList[i*3+2].setDisabled(False)
        for i in range(int(self.CharactersDict[Num].DataDict["NumOrders"]), 15):
            self.OrderEditsList[i*3].setDisabled(True)
            self.OrderEditsList[i*3+1].setDisabled(True)
            self.OrderEditsList[i*3+2].setDisabled(True)
        self.UpdatingCheckbox = True
        if self.CurLoadedChar not in self.AutoLoadDict[self.CurLoadedPos]:
            self.AutoLoadLastOrders.setChecked(False)
        else:
            self.AutoLoadLastOrders.setChecked(True)
        self.UpdatingCheckbox = False

        if self.CharactersDict[Num].DataDict["Vision"] != "0":
            self.LoadMap(self.CharactersDict[Num].DataDict["MapName"], Num)
            try:
                self.MapGraphicsView.MapScene.removeItem(self.SquareHighlight)
            except:
                pass
            self.SquareHighlight = QtWidgets.QGraphicsRectItem(QtCore.QRectF((self.CurCharXPos-1)*self.MapGraphicsView.ZoomLevel, (self.CurCharYPos-1)*self.MapGraphicsView.ZoomLevel, self.MapGraphicsView.ZoomLevel, self.MapGraphicsView.ZoomLevel))
            self.SquareHighlight.setBrush(QtGui.QBrush(QtGui.QColor(51, 204, 255, 100)))
            self.MapGraphicsView.MapScene.addItem(self.SquareHighlight)
            self.MapGraphicsView.ensureVisible(self.SquareHighlight)
            self.MapDataIndex = ((int(self.CurCharXPos)-1)+(int(self.CurCharYPos)-1)*int(self.MapsDict[self.CharactersDict[Num].DataDict["MapName"]].DataList[0]))*5+2
            
            self.CharMap = self.CharactersDict[Num].DataDict["MapName"]
            self.CurSquareData = self.TerrainKeys[self.MapsDict[self.CharMap].DataList[self.MapDataIndex]].split("^")
            self.formattedDisplay = self.CharactersDict[Num].DataDict["MapDisplayName"]
            idx = self.formattedDisplay.rfind(": ")
            if idx != -1:
                self.formattedDisplay = self.formattedDisplay[:idx]
            if ': ' in self.formattedDisplay:
                self.MapNameLabel.setText(self.formattedDisplay.split(': ')[0])
                self.CunningOtherMapName.setText(self.formattedDisplay.split(': ')[1])
            else:
                self.MapNameLabel.setText(self.formattedDisplay)
                self.CunningOtherMapName.setText('')
            self.TerrainTypeLabel.setText(f"{self.CurSquareData[2]}")
            self.MovementPointsValue.setText(self.CurSquareData[3].split()[1])
            self.VisionAdjustmentValue.setText(self.CurSquareData[4].split(": ")[1])
            self.AttackAdjustmentLabel_2.setText(self.CurSquareData[5].split(": ")[1])
            self.DefenceAdjustmentLabel_2.setText(self.CurSquareData[6].split(": ")[1])
            try: #Update sector info
                self.CharactersCreatures_2.clear()
                self.SelectedSquareChars = self.MapsDict[self.CurLoadedMap].VisibleCharacters[int(self.CurCharXPos-1)+int(self.CurCharYPos-1)*int(self.MapsDict[self.CurLoadedMap].DataList[0])+1]
                self.CharactersCreatures_2.addItem(f"{self.CharactersDict[Num].DataDict['Class']} - {self.CharactersDict[Num].DataDict['Name']} ({Num})")
                for i in self.SelectedSquareChars: #Add characters from position
                    if i[5] in self.CharactersList and str(Num) != i[5]:
                        if i[2] == 'R.I.P.':
                            self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} {i[2]} ({i[5]})")
                        else:
                            self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} ({i[5]})")
                for i in self.SelectedSquareChars: #Add all other characters
                    if i[5] not in self.CharactersList:
                        if i[2] == 'R.I.P.':
                            self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} {i[2]} ({i[5]})")
                        else:
                            self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} ({i[5]})")
            except:
                self.CharactersCreatures_2.clear()
            try:
                self.Items.clear()
                self.SelectedSquareItems = self.localItems[int(self.CurCharXPos-1)+int(self.CurCharYPos-1)*int(self.MapsDict[self.CurLoadedMap].DataList[0])+1]
                for i in self.SelectedSquareItems:
                    self.Items.addItem(f"{i[0]} - {i[1]}")
            except:
                self.Items.clear()

            self.goldShown = True
            self.itemsShown = True
            self.charsShown = True
            self.shadersShown = True
            self.showGold()
            self.showItems()
            self.showChars()
            self.MapGraphicsView.showOverlay()
        else:
            show_warning_popup(f"No map data found.\nMap loading will be skipped.")
            #show_warning_popup(f"The map has temporarily been disabled while we work on new logic.\nApologies for inconvenience, please do not report this as a bug.")
            self.CurLoadedMap = "None"
            self.MapGraphicsView.drawMap()

        self.LoadOrders("Data/Current Orders/" + self.CurLoadedChar)
        for i in range(0, 15):
            if self.OrderEditsList[i*3].text() == "":
                self.OrderEditsList[i*3].setFocus()
                break
            elif i == 14:
                if self.OrderEditsList[i*3+1].text() == "":
                    self.OrderEditsList[i*3+1].setFocus()
                else:
                    self.OrderEditsList[i*3+2].setFocus()

        #self.print_all_items()
        #self.print_all_skills()
        

    def LoadMap(self, Map, Num):
        self.CurCharXPos = int(float(self.CharactersDict[Num].DataDict["XPos"]))
        self.CurCharYPos = int(float(self.CharactersDict[Num].DataDict["YPos"]))

        if Map == "Kingdom of Bereny3" and self.CurLoadedMap != Map:
            self.MapGraphicsView.drawMap(self.MapsDict[Map].DataList, self.MapsDict[Map].VisibleSquares, self.MapsDict[Map].VisibleCharacters, self.CurCharXPos, self.CurCharYPos, True)
        elif Map != "Kingdom of Bereny3":
            self.MapGraphicsView.drawMap(self.MapsDict[Map].DataList, self.MapsDict[Map].VisibleSquares, self.MapsDict[Map].VisibleCharacters, self.CurCharXPos, self.CurCharYPos)
        self.CurLoadedMap = Map

        QtCore.QTimer.singleShot(0, self.CentreMap)
        self.MapGraphicsView.LoadChar(self.CurCharXPos-1,self.CurCharYPos-1,self.CharGraphicList[0],self.CharGraphicList[1])

    def CentreMap(self):
        self.MapGraphicsView.centerOn(self.SquareHighlight)

    def eventFilter(self, source, event):
        """Capture MapScene mouse events and change selected square on left click without drag. Map scrolling is handled in the MapGraphics class.
           Create highlight for selected square.
           Update terrain info for selected square."""
        if source == self.MapGraphicsView.MapScene:
            if event.type() == QtCore.QEvent.Type.GraphicsSceneMousePress or  event.type() == QtCore.QEvent.Type.GraphicsSceneMouseRelease:
                try:
                    if self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
                        # Check for left click without drag.
                        if event.button() == QtCore.Qt.MouseButton.LeftButton and event.type() == QtCore.QEvent.Type.GraphicsSceneMousePress:
                            self.StartX = QtGui.QCursor().pos().x()
                            self.StartY = QtGui.QCursor().pos().y()
                        if event.button() == QtCore.Qt.MouseButton.LeftButton and event.type() == QtCore.QEvent.Type.GraphicsSceneMouseRelease:
                            self.EndX = QtGui.QCursor().pos().x()
                            self.EndY = QtGui.QCursor().pos().y()
                            self.XDist = self.StartX - self.EndX
                            self.YDist = self.StartY - self.EndY
                            if abs(self.XDist) < 5 and abs(self.YDist) < 5:
                                self.SelectedX = math.floor(event.scenePos().x()/self.MapGraphicsView.ZoomLevel)
                                self.SelectedY = math.floor(event.scenePos().y()/self.MapGraphicsView.ZoomLevel)
                                try:
                                    self.MapGraphicsView.MapScene.removeItem(self.SquareHighlight)
                                except:
                                    pass
                                #Create square highlight and centre map.
                                self.SquareHighlight = QtWidgets.QGraphicsRectItem(QtCore.QRectF(self.SelectedX*self.MapGraphicsView.ZoomLevel, self.SelectedY*self.MapGraphicsView.ZoomLevel, self.MapGraphicsView.ZoomLevel, self.MapGraphicsView.ZoomLevel))
                                self.SquareHighlight.setBrush(QtGui.QBrush(QtGui.QColor(51, 204, 255, 100)))
                                self.MapGraphicsView.MapScene.addItem(self.SquareHighlight)
                                if self.shadersShown == False:
                                    self.SquareHighlight.hide()
                                self.MapGraphicsView.centerOn((self.SelectedX+1)*self.MapGraphicsView.ZoomLevel-self.MapGraphicsView.ZoomLevel/2, (self.SelectedY+1)*self.MapGraphicsView.ZoomLevel-self.MapGraphicsView.ZoomLevel/2)
                                #Update terrain info.
                                self.MapDataIndex = (int(self.SelectedX)+int(self.SelectedY)*int(self.MapsDict[self.CurLoadedMap].DataList[0]))*5+2
                                self.SquareKey = self.MapsDict[self.CurLoadedMap].DataList[self.MapDataIndex]
                                if self.SquareKey == "0.0" or self.SquareKey == "0":
                                    self.TerrainTypeLabel.setText("Unidentified")
                                    self.MovementPointsValue.setText("???")
                                    self.VisionAdjustmentValue.setText("???")
                                    self.AttackAdjustmentLabel_2.setText("???")
                                    self.DefenceAdjustmentLabel_2.setText("???")
                                else:
                                    self.CurSquareData = self.TerrainKeys[self.SquareKey].split("^")
                                    self.TerrainTypeLabel.setText(f"{self.CurSquareData[2]}")
                                    self.MovementPointsValue.setText(self.CurSquareData[3].split()[1])
                                    self.VisionAdjustmentValue.setText(self.CurSquareData[4].split(": ")[1])
                                    self.AttackAdjustmentLabel_2.setText(self.CurSquareData[5].split(": ")[1])
                                    self.DefenceAdjustmentLabel_2.setText(self.CurSquareData[6].split(": ")[1])
                                    try: #Update sector info
                                        self.CharactersCreatures_2.clear()
                                        self.SelectedSquareChars = self.MapsDict[self.CurLoadedMap].VisibleCharacters[int(self.SelectedX)+int(self.SelectedY)*int(self.MapsDict[self.CurLoadedMap].DataList[0])+1]
                                        for i in self.SelectedSquareChars:
                                            if self.CurLoadedChar == i[5]:
                                                self.CharactersCreatures_2.addItem(f"{self.CharactersDict[self.CurLoadedChar].DataDict['Class']} - {self.CharactersDict[self.CurLoadedChar].DataDict['Name']} ({self.CurLoadedChar})")
                                        for i in self.SelectedSquareChars: #Add characters from position
                                            if i[5] in self.CharactersList and i[5] != str(self.CurLoadedChar):
                                                if i[2] == 'R.I.P.':
                                                    self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} {i[2]} ({i[5]})")
                                                else:
                                                    self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} ({i[5]})")
                                        for i in self.SelectedSquareChars: #Add all other characters
                                            if i[5] not in self.CharactersList:
                                                if i[2] == 'R.I.P.':
                                                    self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} {i[2]} ({i[5]})")
                                                else:
                                                    self.CharactersCreatures_2.addItem(f"{i[0]} - {i[1]} ({i[5]})")
                                    except: #Update sector info items
                                        self.CharactersCreatures_2.clear()
                                    try:
                                        self.Items.clear()
                                        self.SelectedSquareItems = self.localItems[int(self.SelectedX)+int(self.SelectedY)*int(self.MapsDict[self.CurLoadedMap].DataList[0])+1]
                                        for i in self.SelectedSquareItems:
                                            self.Items.addItem(f"{i[0]} - {i[1]}")
                                    except:
                                        self.Items.clear()
                except:
                    pass
        return super().eventFilter(source, event)

    def LastCharacter(self):
        if self.PositionLoaded:
            modifiers = QtGui.QGuiApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
                self.ctrl_LastCharacter()
            else:
                if self.CurCharIndex == 1:
                    self.CurCharIndex = len(self.CharactersList)
                else:
                    self.CurCharIndex -= 1
                self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])

    def ctrl_LastCharacter(self):
        if self.PositionLoaded:
            self.SaveOrders()
            for i in range(self.CurCharIndex, 0, -1):
                try:
                    self.OrdersFile = open("Data/Current Orders/" + self.CharactersDict[self.CharactersList[i-1]].DataDict["Number"], 'rb')
                    self.OrdersString = self.OrdersFile.read().hex()
                    self.OrdersFile.close()
                    self.OrdersString = [self.OrdersString[i:i+8] for i in range(0, len(self.OrdersString), 8)]
                    for j in range(0, int(self.CharactersDict[self.CharactersList[i-1]].DataDict["NumOrders"])):
                        if self.OrdersString[j*3] == "00cdcdcd":
                            self.CurCharIndex = i
                            self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                            return
                except:
                    self.CurCharIndex = i
                    self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                    return
            for i in range(len(self.CharactersList), self.CurCharIndex, -1):
                try:
                    self.OrdersFile = open("Data/Current Orders/" + self.CharactersDict[self.CharactersList[i-1]].DataDict["Number"], 'rb')
                    self.OrdersString = self.OrdersFile.read().hex()
                    self.OrdersFile.close()
                    self.OrdersString = [self.OrdersString[i:i+8] for i in range(0, len(self.OrdersString), 8)]
                    for j in range(0, int(self.CharactersDict[self.CharactersList[i-1]].DataDict["NumOrders"])):
                        if self.OrdersString[j*3] == "00cdcdcd":
                            self.CurCharIndex = i
                            self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                            return
                except:
                    self.CurCharIndex = i
                    self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                    return
            self.LoadCharDialog = MessageDialog("No characters on this position are missing orders.", "All orders complete", self)
            self.LoadCharDialog.exec()

    def NextCharacter(self):
        if self.PositionLoaded:
            modifiers = QtGui.QGuiApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
                self.ctrl_NextCharacter()
            else:
                if self.CurCharIndex == len(self.CharactersList):
                    self.CurCharIndex = 1
                else:
                    self.CurCharIndex += 1
                self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])

    def ctrl_NextCharacter(self):
        if self.PositionLoaded:
            self.SaveOrders()
            for i in range(self.CurCharIndex, len(self.CharactersList) + 1):
                try:
                    self.OrdersFile = open("Data/Current Orders/" + self.CharactersDict[self.CharactersList[i-1]].DataDict["Number"], 'rb')
                    self.OrdersString = self.OrdersFile.read().hex()
                    self.OrdersFile.close()
                    self.OrdersString = [self.OrdersString[i:i+8] for i in range(0, len(self.OrdersString), 8)]
                    for j in range(0, int(self.CharactersDict[self.CharactersList[i-1]].DataDict["NumOrders"])):
                        if self.OrdersString[j*3] == "00cdcdcd":
                            self.CurCharIndex = i
                            self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                            return
                except:
                    self.CurCharIndex = i
                    self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                    return
            for i in range(1, self.CurCharIndex):
                try:
                    self.OrdersFile = open("Data/Current Orders/" + self.CharactersDict[self.CharactersList[i-1]].DataDict["Number"], 'rb')
                    self.OrdersString = self.OrdersFile.read().hex()
                    self.OrdersFile.close()
                    self.OrdersString = [self.OrdersString[i:i+8] for i in range(0, len(self.OrdersString), 8)]
                    for j in range(0, int(self.CharactersDict[self.CharactersList[i-1]].DataDict["NumOrders"])):
                        if self.OrdersString[j*3] == "00cdcdcd":
                            self.CurCharIndex = i
                            self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                            return
                except:
                    self.CurCharIndex = i
                    self.LoadCharacter(self.CharactersList[self.CurCharIndex-1])
                    return
            self.LoadCharDialog = MessageDialog("No characters on this position are missing orders.", "All orders complete", self)
            self.LoadCharDialog.exec()
        

    def GetPixmap(self, BMPNum, BMPPos, Size): #Helper function to return a pixmap of a graphic from the two bmp numbers, we also set black to be transparent
        self.rect = QtCore.QRect(((int(BMPPos)-1)%10)*32, int((int(BMPPos)-1)/10)*32, 32, 32)
        self.full_bmp = QtGui.QImage("Resources/Program Graphics/C32_"+str(BMPNum)+".bmp").copy(self.rect)
        self.full_bmp = self.full_bmp.convertToFormat(QtGui.QImage.Format.Format_ARGB32)
        self.ptr = self.full_bmp.bits()
        self.ptr.setsize(4096)
        self.arr = np.array(self.ptr).reshape(32, 32, 4)
        self.black_mask = np.all(self.arr[:, :, :3] == [0, 0, 0], axis=-1)
        self.arr[self.black_mask, 3] = 0
        self.full_bmp = QtGui.QImage(self.arr.data, 32, 32, 128, QtGui.QImage.Format.Format_ARGB32)
        
        return QtGui.QPixmap.fromImage(self.full_bmp).scaled(Size, Size)

    def hideGold(self):
        self.MapGraphicsView.hideGold()

    def showGold(self):
        self.MapGraphicsView.showGold()

    def hideItems(self):
        self.MapGraphicsView.hideItems()

    def showItems(self):
        self.MapGraphicsView.showItems()

    def hideChars(self):
        self.MapGraphicsView.hideChars()

    def showChars(self):
        self.MapGraphicsView.showChars(self.CurCharXPos-1,self.CurCharYPos-1)

    def toggleGold(self):
        if self.PositionLoaded and self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
            if self.goldShown == True:
                self.hideGold()
                self.goldShown = False
            else:
                self.showGold()
                self.goldShown = True

    def toggleItems(self):
        if self.PositionLoaded and self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
            if self.itemsShown == True:
                self.hideItems()
                self.itemsShown = False
            else:
                self.showItems()
                self.itemsShown = True

    def toggleChars(self):
        if self.PositionLoaded and self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
            if self.charsShown == True:
                self.hideChars()
                self.charsShown = False
            else:
                self.showChars()
                self.charsShown = True

    def toggleShaders(self):
        if self.PositionLoaded and self.CharactersDict[self.CurLoadedChar].DataDict["Vision"] != "0":
            if self.shadersShown == True:
                try:
                    self.SquareHighlight.hide()
                except:
                    pass
                self.shadersShown = False
                self.MapGraphicsView.hideOverlay()
            else:
                try:
                    self.SquareHighlight.show()
                except:
                    pass
                self.shadersShown = True
                self.MapGraphicsView.showOverlay()
    

class ChoosePositionDialog(QtWidgets.QDialog):
    
    def __init__(self, parent=None): #Creates the dialog for the user to select a position number
        super().__init__(parent)

        self.setWindowTitle("Choose Position Number to Load")

        self.combo_box = QtWidgets.QComboBox(self) #Create the combo box which the user can select the number from
        self.combo_box.addItems([i for i in parent.PosNumberDict])

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel, self) #Creates the buttons to close the dialog with confirm or cancel
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout() #Creates the layout for the dialog
        self.layout.addWidget(self.combo_box)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def get_selected_number(self): #Returns the currently selected number
        return int(self.combo_box.currentText())

class FindCharacterDialog(QtWidgets.QDialog):
    def __init__(self, number_list, position, callback_function, parent=None):
        super().__init__(parent)
        self.number_list = number_list
        self.position = position
        self.callback_function = callback_function
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Enter Character Number')
        
        # Set up the layout
        layout = QtWidgets.QVBoxLayout()

        # Create a QLabel for instructions
        self.label = QtWidgets.QLabel("Please enter the character number to be found:")
        self.label.setStyleSheet("color: black;")
        layout.addWidget(self.label)

        # Create a QLineEdit for number input
        self.line_edit = QtWidgets.QLineEdit(self)
        layout.addWidget(self.line_edit)

        # Create a QLabel for error messages
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

        # Create a QDialogButtonBox for confirm and cancel buttons
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.check_number)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def check_number(self):
        try:
            number = self.line_edit.text()
            if number in self.number_list:
                index = self.number_list.index(number)
                self.callback_function(number, index)
                self.accept()
            else:
                self.error_label.setText("Character " + number + " not found on position " + self.position + ".")
        except ValueError:
            self.error_label.setText("Invalid input. Please enter a valid number.")

class MessageDialog(QtWidgets.QDialog):
    def __init__(self, message, title, parent=None):
        super().__init__(parent)
        self.message = message
        self.title = title
        self.time = time
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        
        # Set up the layout
        layout = QtWidgets.QVBoxLayout()

        # Create a QLabel for the message
        self.label = QtWidgets.QLabel(self.message, self)
        self.label.setStyleSheet("color: black;")
        layout.addWidget(self.label)

        # Create an OK button
        self.ok_button = QtWidgets.QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

class Character: #Simple class for storing all data on each character as a dictionary
    def __init__(self):
        self.DataDict = {}

    def add_data(self, key, value):
        self.DataDict[key] = value

class GameMap: #Simple class for storing all data from each map as a dictionary
    """Store required data for each map of loaded position.

    Variables:
    self.DataList - A list contining all the data for that map, this is the values in the data file split on "^" to give the list elements.
    self.VisibleSquares - A set 
    """
    
    def __init__(self):
        self.DataList = []
        self.VisibleSquares = set()
        self.VisibleCharacters = {}

    def add_data(self, value):
        self.DataList.append(value)

    def add_Visible(self, value):
        self.VisibleSquares.add(value)

    def add_Character(self, key, value):
        if key not in self.VisibleCharacters:
            self.VisibleCharacters[key] = []
        if value not in self.VisibleCharacters[key]:
            self.VisibleCharacters[key].append(value)

class FocusTracker(QtCore.QObject):
    """Track which line edit was last focussed and listen for keyboard presses."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_focused_widget = None

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.FocusIn and obj in window.OrderEditsList:
            if isinstance(obj, (QtWidgets.QLineEdit)):
                self.last_focused_widget = obj
        elif event.type() == QtCore.QEvent.Type.KeyPress:
            if not window.Loading:
                if window.PositionLoaded and window.CharactersDict[window.CurLoadedChar].DataDict["Vision"] != "0":
                    key_event = event
                    if key_event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        if key_event.key() in (QtCore.Qt.Key.Key_Plus, QtCore.Qt.Key.Key_Equal):
                            factor = 1.25
                            window.MapGraphicsView._zoom += 1
                            if window.MapGraphicsView._zoom >= window.MapGraphicsView.min_zoom and window.MapGraphicsView._zoom <= window.MapGraphicsView.max_zoom:
                                window.MapGraphicsView.scale(factor, factor)
                            elif window.MapGraphicsView._zoom <= window.MapGraphicsView.max_zoom:
                                window.MapGraphicsView._zoom = window.MapGraphicsView.min_zoom
                            else:
                                window.MapGraphicsView._zoom = window.MapGraphicsView.max_zoom
                            return True
                        elif key_event.key() == QtCore.Qt.Key.Key_Minus:
                            factor = 0.8
                            window.MapGraphicsView._zoom -= 1
                            if window.MapGraphicsView._zoom >= window.MapGraphicsView.min_zoom and window.MapGraphicsView._zoom <= window.MapGraphicsView.max_zoom:
                                window.MapGraphicsView.scale(factor, factor)
                            elif window.MapGraphicsView._zoom <= window.MapGraphicsView.max_zoom:
                                window.MapGraphicsView._zoom = window.MapGraphicsView.min_zoom
                            else:
                                window.MapGraphicsView._zoom = window.MapGraphicsView.max_zoom
                            return True
                        elif key_event.key() == QtCore.Qt.Key.Key_Space:
                            tempZoom = window.MapGraphicsView._zoom + 3
                            window.MapGraphicsView._zoom = -3
                            factor = 0.8**tempZoom
                            window.MapGraphicsView.scale(factor, factor)
                            window.MapGraphicsView.centerOn((window.CurCharXPos)*window.MapGraphicsView.ZoomLevel-window.MapGraphicsView.ZoomLevel/2, (window.CurCharYPos)*window.MapGraphicsView.ZoomLevel-window.MapGraphicsView.ZoomLevel/2)
                            return True
        return super().eventFilter(obj, event)

def except_hook(exc_type, exc_value, exc_traceback):
    """Custom exception handler.

    Log the exception to a file, and create a dialog to inform the user, also allowing them to close out the program.
    """
    
    error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)) # Format the exception traceback
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    with open(f"Error Logs/error_log_{timestamp}.txt", "a") as log_file: # Log the error to a file
        log_file.write(error_details)

    # Create a PyQt6 error dialog
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    msg.setWindowTitle("Application Error")
    msg.setText("An unexpected error occurred.")
    msg.setInformativeText("A log of the error has been created in the Error Logs folder.")
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Close)
    msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Close)
    
    response = msg.exec() # Show the dialog
    sys.exit(1) # Exit the program

def derive_key(account_number: int) -> bytes:

    master = secure_key.get_master_key()

    data = master + str(account_number).encode()

    return hashlib.sha256(data).digest()    

def check_for_update():
    """Check program version against release version to check for update.

    """
    try:
        response = requests.get("https://hurstnettech.github.io/NVE-Updates/version.json", timeout=5)
        data = response.json()
        latest_version = data["latest_version"]
        return latest_version != __version__
    except:
        return False



if __name__ == "__main__": #Code run on program start

    with open('settings.txt') as f:
        SettingsData = f.readlines()
        SettingsDict = {}
        for i in SettingsData:
            SettingsDict[i.split(": ")[0]] = i.split(": ")[1].strip()

    if "Custom" in SettingsDict["scaling"]:
        window_scaling = str(int(SettingsDict["scaling"].split()[1]) / 100)
    else:
        window_scaling = str(int(re.match(r"(\d+)", SettingsDict["scaling"]).group(1)) / 100)

    os.environ["QT_SCALE_FACTOR"] = window_scaling

    app = QtWidgets.QApplication(sys.argv)

    pixmap = QtGui.QPixmap("Resources/Program Graphics/NVE2.0_Splash_Screen.jpg")
    splash = QtWidgets.QSplashScreen(pixmap)
    #splash.showMessage("Loading...", QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignCenter)
    splash.show()

    app.processEvents()

    __version__ = "1.021"
    updateAvailable = check_for_update()

    hostname = str(script_Connection.get_host()) # Connection info
    port = 22
    username = str(script_Connection.get_username())
    password = str(script_Connection.get_password())

    BaseKey = secure_key.get_master_key()
    
    with open('Data/Server Turn Num.txt') as f:
        DataCheck = f.readlines()


    if DataCheck == ['0']:
        window = FirstSetup() 
        window.show()
        window.setWindowTitle("NVE First Setup")

        splash.finish(window)

        sys.exit(app.exec())
        
        #app.exec()
        
    else:
        AccNum = load_encrypted_text('Data/Account Verification.txt', 'Data/Account Verification.dat', BaseKey).split(" - ")[0]
        #with open('Data/Account Verification.txt') as f:
            #AccNum = f.readlines()[0].split(" - ")[0]



        EncKey = derive_key(AccNum)        
        window = MainWindow()
        window.show()
        window.setWindowTitle("NVE 2.0")

        splash.finish(window)

        sys.exit(app.exec())
        
        #app.exec()
            
