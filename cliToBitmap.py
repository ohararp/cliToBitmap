# -*- coding: utf-8 -*-
"""

High Level Concept - Read and store interior and exterior contours from CLI
into an image.  These images are then Boolean'd together to form the final
output image which is Black for Solid and White for Nothing. 

@author: Ryan O'Hara 
@email: ryanohara@ntopology.com
@data: 20190528
@Anaconda Distribution 3.7.2

Function Call - # run cliToBitmap.py 0.XXX
-Where 0.XXX is the Pixel Resoluion in 1 Pixel = 0.XXX MM

Input 1 - CLI file
Input 2 - Pixel Resolution in MM
Output  - Zip File of 8-Bit BMP Image Stack 

*Note if you receive error "PyNoAppError: The wx.App object must be created first!"
Close Console and Re-run
"""


#%%----------------------------------------------------------------------------
# Start The Modules
#%%----------------------------------------------------------------------------
import os
import wx  
import numpy as np
import math
import pygame
from pygame import gfxdraw
import cv2
import zipfile
import shutil
import sys

# run cliToBitmap.py 0.1
pixelResolutionMM = float(sys.argv[1])
# Compute Dimensions in Pixels based on pixel resolution
#pixelResolutionMM=0.05 #50 um per pixel
#%%----------------------------------------------------------------------------
# Use Gui to Grab Data Files
#%%----------------------------------------------------------------------------
fname=''

app = wx.App()
# Create a Gui Window for opening the file
fdialog = wx.FileDialog(None, 'Open CLI Data File ...', wildcard='*.cli',style=wx.DD_DEFAULT_STYLE)
succ = fdialog.ShowModal()
        
if (succ == wx.ID_OK):
    path = fdialog.GetDirectory()#.encode(encoding='UTF-8')
    fname = fdialog.GetFilename()#.encode(encoding='UTF-8')

# Destroy the Dialog so script does not hang
fdialog.Destroy()

# Delete the App after file found
del app

# Change to Path Directory
os.chdir(path)

# Get just Text in front of file extension
fnameDot=fname[0:fname.find('.')]

#%%----------------------------------------------------------------------------
# Poly Area SubFunction
#%%----------------------------------------------------------------------------        
def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

#%%----------------------------------------------------------------------------
# Setup Global Variable
#%%----------------------------------------------------------------------------
x=[0]
y=[0]
pi=math.pi

#%%----------------------------------------------------------------------------
# Pre-Allocate Global Arrays
#%%----------------------------------------------------------------------------
# Pre-Allocate Global Arrays
lineCtr=0 #Files Start at Line 1
lineNo=np.array([])
lineAreaMM2=np.array([])
totalIntExtTest=np.array([])
lineDistMM=np.array([])
layerHt=0
layerHts=np.array([])
layerNo=np.array([])
layerAreaMM2=np.array([])
layerCtr=-1 # We Index At First sighting so need a -1 
layerLineCtr=0

xPts=[]
yPts=[]
ptsTotal=[]

# Open the Selected File
f=open(fname,"r")
print('Reading %s' % fname)

# Loop Through CLi Files to a limited wet of points
# Eventually replace with a While Loop to EOF
while 1:
    #  Read A Line of Data
    line=f.readline()
    # Increment Line Counter
    lineCtr=lineCtr+1
    print (".", end = '')

    
    # Get Unit Scaling Factor from File
    if line.find('$$UNITS/') == 0:
        a=line.find("/")+1
        b=line.find("\n")
        unitFactor=float(line[a:b])
        
    # Test Bounding Box $$DIMENSION/x1,y1,z1,x2,y2,z2 
    if line.find('$$DIMENSION/') == 0:
        # Get Dimension Data
        a=line.find("/")+1
        b=line.find("\n")
        dimensionsMM=[float(i) for i in line[a:b].split(',')]
        xOffsetMM=0
        yOffsetMM=0
        
        # Get Dimension Data in MM
        Wmm=abs(dimensionsMM[0])+dimensionsMM[3]
        Hmm=abs(dimensionsMM[1])+dimensionsMM[4]
        
        W=int(Wmm/pixelResolutionMM)
        H=int(Hmm/pixelResolutionMM)
        
        # Define Colors for Images
        white=[255,255,255]
        black=[0,0,0]

        # Name Temporary Images
        imageNameInt=("CLI-INT.bmp")
        imageNameExt=("CLI-EXT.bmp")
        
        # Create Image Instances 
        imageInt = pygame.Surface((W, H))
        imageInt.fill(white)
        imageExt = pygame.Surface((W, H))
        imageExt.fill(white)
        
        # Get Offset of Data so Values are always positive
        # Scale based on unitFactor Conversion
        if dimensionsMM[0] < 0:
            xOffsetMM=dimensionsMM[0]
            pixelOffsetX=int(abs(dimensionsMM[0])/pixelResolutionMM)
            
        if dimensionsMM[1] < 0:
            yOffsetMM=dimensionsMM[1]
            pixelOffsetY=int(abs(dimensionsMM[1])/pixelResolutionMM)
            
 
        # Check if a Dummy folder exists in Path Directory
        if os.path.exists(path + '\\temp'):
            shutil.rmtree(path + '\\temp') # Remove the directory if it exists
                    
        # Change Directory to Dummy
        os.mkdir(path + '\\temp')
        os.chdir(path + '\\temp')
        print(os.getcwd())

    # Test if this Line is a Layer
    if line.find('$$LAYER/') == 0 or line.find('$$GEOMETRYEND') == 0:
           
        # Save Image Data Because New Layer
        if layerCtr > -1:
            # Save the Layer Images
            pygame.image.save(imageInt, imageNameInt)
            pygame.image.save(imageExt, imageNameExt)
            
            # Open a copy of the Previously Saved Images
            cvImgInt=cv2.imread(imageNameInt)
            cvImgExt=cv2.imread(imageNameExt)
            
            # Merge the Interior and Exterior Images
            mrg = cv2.bitwise_xor(cvImgExt,cvImgInt)
            # Invert the IMages
            flip = cv2.bitwise_not(mrg)
            #Get the Layer Image Name
            layerImageName=("%s-%dx%d-%06d.bmp" % (fnameDot,W,H,layerCtr))
            # Write the Images
            cv2.imwrite(layerImageName,flip)
            print()
            print(layerImageName)
            # Remove any OpenCV Windows
            cv2.destroyAllWindows()
            
            # New Layer Found - Get Layer Height Value and Blank Temp Image            
            if line.find('$$LAYER/') == 0:
                a=line.find("/")+1
                b=line.find("\n")
                layerHt=float(line[a:b])
                print("Blanking Images")
                pygame.gfxdraw.filled_polygon(imageInt,[(0,0),(0,H),(H,H),(H,0)],white)
                pygame.gfxdraw.filled_polygon(imageExt,[(0,0),(0,H),(H,H),(H,0)],white)
        
        # Terminate if End of the File is Found        
        if line.find('$$GEOMETRYEND') == 0:
            os.remove(imageNameInt)
            os.remove(imageNameExt)
            break
        layerCtr=layerCtr+1
        
    # Test if this line is a Polyline
    lineTest = line.find('$$POLYLINE/1')

    if lineTest==0:
        layerLineCtr=layerLineCtr+1
        # Get all of the data in the line
        columns=line.split(",")
        # Test to see if Interior or Exterior Polyline (0=Interior 1=Exterior)
        if float(columns[1])==0:
            intExtTest =-1
        else:
            intExtTest = 1
        totalIntExtTest=np.append(totalIntExtTest,intExtTest)
        
        # Get all of the data in the line
        columns=line.split(",")
        # Only the points we care about omit first 3 data entries
        pts=columns[3:]
        # Length of all the pts divided by 2
        ptsTotal.append(len(pts))
        
        # Get Indexes for Easier writing of Point Pairs
        xIdx=list(range(0,len(pts),2))
        yIdx=list(range(1,len(pts),2))
        
        # Initialize Numpy Array for X and Y For Every Line
        npx=np.array([0]*len(xIdx))               
        npy=np.array([0]*len(yIdx))
        
        npxPix=np.array([0]*len(xIdx))               
        npyPix=np.array([0]*len(yIdx))
        npxMM=npx
        npyMM=npy
        
        # Generate Pt lists for Json
        for n in range(0,len(xIdx)):
            # Assign X and Y Data to Numpy Array
            npx[n]=int(pts[xIdx[n]])
            npy[n]=int(pts[yIdx[n]])
            
            xPts.append(pts[xIdx[n]])
            yPts.append(pts[yIdx[n]])
            
        
        # Scale Numpy Output Based on Unitfactor
        npxMM=npx*unitFactor
        npyMM=npy*unitFactor
        
        # Scale Numpy MM to Pixels - Uses Unit Factor and Pixel Resolution
        npxPix = np.round(npx*unitFactor/pixelResolutionMM+pixelOffsetX)
        npyPix = np.round(npy*unitFactor/pixelResolutionMM+pixelOffsetY)
        
        # Calculate Line Area
        lineAreaMM2=np.append(lineAreaMM2,PolyArea(npxMM,npyMM)*intExtTest)
        
        # Store Line Number Data
        lineNo=np.append(lineNo,lineCtr)
        
        # Store Layer Number and Height with Every Line
        layerNo=np.append(layerNo,layerCtr)
        layerHts=np.append(layerHts,layerHt)
        
        # Form Pt Pairs from X-Y pts in 2 arrays 
        ptPairs=np.column_stack((npxMM,npyMM))
        # Init Distance Array
        distSeg=np.array([0]*len(xIdx)) 
        # Loop Through all the Pts Calculating the Euclidean Distance
        for n in range(0,len(xIdx)-1):
            a=ptPairs[n,]
            b=ptPairs[n+1,]
            distSeg = np.append(distSeg,np.linalg.norm(a-b))
        lineDistMM=np.append(lineDistMM,sum(distSeg))

        # Define Minimum Area for Valid Test Criteria
        lineAreaThreshold=0.1
        # Pre-Allocate Validity Array - Set All Invalid Initially
        lineAreaValidIdx=np.zeros(len(lineAreaMM2))
        for n in range(0,len(lineAreaMM2)):
            if abs(lineAreaMM2[n])>lineAreaThreshold:
                lineAreaValidIdx[n]=1

        # Write Polygon Data to Image
        if intExtTest == -1: #interior contour
            # Interior Image
            pygame.gfxdraw.filled_polygon(imageInt,tuple(zip(npxPix,npyPix)),black)
        else:
            # Exterior Image
            pygame.gfxdraw.filled_polygon(imageExt,tuple(zip(npxPix,npyPix)),black)

# Close the Cli File
f.close()

# List Files in dummy directory
files = os.listdir(os.getcwd())

# Check if a New Zip folder exists in Path Directory
# Remove the file if it exists
zipName=("%s-%dx%d.zip" % (fnameDot,W,H))

if os.path.exists(path + '\\'+ zipName):
    os.remove(path + '\\'+ zipName) 
    print("Old Zip File Deleted - %s" % zipName)

# Zip Up Dummy Directory        
files = os.listdir(os.getcwd())
zip = zipfile.ZipFile(path + '\\'+("%s-%dx%d.zip" % (fnameDot,W,H)), 'w') 
for x in range (len(files)):
    zip.write(files[x])
zip.close()
print("New Zip File Written - %s" % zipName)

# Delete Zip Variable
del zip

# Go Back to Path Directory
os.chdir(path)

# Check if a Dummy folder exists in Path Directory
if os.path.exists("temp"):
    shutil.rmtree("temp") # Remove the directory if it exists
    
print("Done")        
