# VRDR

![Foto-IPG-1-2048x1125](https://github.com/user-attachments/assets/40b123f6-28ae-49b5-80b5-d5e186c0daf6)

## Table of contents
- [Installation](#installation-protocol-vr-goggles)
  - [Smartphone Apps](#smartphone-apps)
    - [Install Meta Horizon App](#install-meta-horizon-app)
    - [Install Duo Mobile Authenticator](#install-duo-mobile-for-authenticator)
  - [PC softwares](#pc-softwares-computer)
    - [Meta Quest Link](#meta-quest-link)
    - [SideQuest](#sidequest)
- [Nanover](#nanover-video_game)

# Installation protocol VR :goggles:

## First Steps:

For installing everything for using VR headset on Windows and your Smarphone. 

## Smartphone Apps

### **Install Meta Horizon App** 
Here we will introduce our credentials

  - **Sign in:** (Same account for Facebook and Meta Oculus)
    - mmlab2024vr@gmail.com
    - `******`
  - When signing in, the app will ask you to introduce a code, that will be sent to:  
    - The mobile number that was set when the account was created.  
    - The Authenticator App you need to set up.
>[!NOTE]
>Since the account already exists you can choose between them. First, the recommendation is to choose the **Mobile number** since you did not set up the [Authenticator](#install-duo-mobile-for-authenticator) yet.
  - If glasses are already connected to the same account, but in a different device (Not a new headset), is not needed to connect the glasses again. The Meta Horizon App will recognize them.

### **Install Duo Mobile for authenticator.** 

For registering a new platform here, we need to have installed already the Meta Quest App in other device.

- Inside Meta Horizon App

- Password and Security -> Two-step authentication.

- **Meta Account** selection
- Authentication App: It will display a QR code that you will use in the next steps.
- Follow the steps to Duo Mobile App
	- Read the QR code with the new device
	- New password for the Duo Mobile Meta Authenticator (This is just for the autenthicator)
	- Next steps inside Meta Horizon App

## PC softwares :computer:
<a id="meta-quest-link"></a>
### [Meta Quest Link](https://www.meta.com/help/quest/1517439565442928/?srsltid=AfmBOooMemUNn7K3bqiH5npCaSyYkRbHkuQEm4DbkLM2XrjGhH0r9AJf): Following default installation. This will allow us to connect the glasses to the PC via Air Link or Wired Link, in that case we need the cable. This is needed to run the Nanover App through PC-VR

- Scroll down to find the **Download App** button 
- Sign in: Through email (not facebook, not instagram)
  - mmlab2024vr@gmail.com
  - `*******`

  - Follow the steps for sign in -> Need the authenticator App
  - Install the VR software (default settings)
  - Two different ways to connect the headset to the app
    - **AirLink**(preferred):
      - Inside the glasses, navigate through the **QuickMenu** by clicking at the bottom tool bar  
    - Wired
  - Once connected to the PC you can also cast your glasses
 
>[!IMPORTANT]
>To display the Meta Quest Link properly it is necessary to go inside the software Meta Quest Link, and set OpenXR Runtime as default for MetaQuest
>**Settings**->**General**->**OpenXR Runtime** 


### [SideQuest](https://sidequestvr.com/):

This software will allow us to install APK files third-party developed (Like *Cyclarity* or *CoronaVRus Coaster*). Also, we can "overclock" the glases to improve performance (Caution with this)

- Once on the webpage look for **Get SideQuest** on the left

- Advanced Installer of SideQuest, following default installation. 


#### **For installing APK:**
- _Connect the glasses through cable to the PC._ It is needed to have the charge cable included (Type C-Type C) or the Quest Link Cable (Buying it, not needed the oficial one) but is Type C-Type A USB.

In case PC has a **USB-C** conector is okay👍 to use it. If not, you need to use the other one. Better if USB-A cable is connected directly to the Motherboard through the back connectors of the computer

- Allow inside glasses the USB-debugging 
- Inside SideQuest, on the top. There are several options. To install an APK file, go to the box with a pointing-down arrow. 
- Drag the APK to SideQuest. Wait until is installed.

>[!NOTE]
**Developer Mode must be ON to allow this. In case creating a new account it is needed to go inside SideQuest and follow the instructions to set up de organisation and turn on the developer mode.**

To check the installation, go on the top to the 9 squared symbol(). There are the apps already installed on the glasses.

**For running the apps:**

- With the controllers or with hand-tracking, select on the bottom right the 9 squared symbol. 
- On the left, you will se a list displaying: All, Applications… If you can see "Unkown Sources Apps", that's it. If not:
- For being able to see the "Unknown Sources Apps" you need to go first inside "Applications", and then on the top select the filters to see the apps you installed in "Unknown Sources".

**For casting the glasses:**

In order to be able to see what is going on inside the glasses without wearing them, you need to cast. There are two ways:

Inside SideQuest you will be able to cast the glasses, either through [SideQuest App](https://sidequestvr.com/) or by [OculusCasting](https://www.oculus.com/casting/). 

For SideQuest casting you need to be wired and click on the top on a tv-with-a-play symbol, this will allow you to select if you want to cast by Stream (SideQuest) or by OculusCasting.

You can also cast through [Oculus Casting](https://www.oculus.com/casting/) avoiding SideQuest

Through you can cast too. Check [Meta Quest Link](#meta-quest-link) on the top

***************


# Nanover :video_game:

   [Github Nanover](https://github.com/IRL2/nanover-server-py)
   
   [Nanover Documentation](https://irl2.github.io/nanover-docs/)

For installing and use Nanover. There are two ways to run it, through PC-VR or with standalone App (installing the APK). 

First, we need to install [Anaconda Navigator](https://www.anaconda.com/download/success) 🐍 and create the environment 

- Anaconda Navigator installation following the default installation settings.
- Once Anaconda is installed, find *Anaconda Powershell Prompt* in your Windows

**Environment creation.**

This environment will give us the tools that Nanover needs to run. Nanover will be used through Jupyter Lab

- Following the steps inside the documentation we can copy and paste the commands, the first one with a slight change since we need to specify the version of the environment.

```conda create -n nanover -c irl -c conda-forge nanover-server=0.1.2768```

>[!NOTE]
>Follow the steps from here of the [documentation](https://irl2.github.io/nanover-docs/).


## Running Nanover :running:

PC-VR:

Once you follow the installation of Nanover itself, you need to install the iMD-VR client.

In a Anaconda Powershell Prompt window, you need to:
- Activate the environment

```conda activate nanover```

- Install the NanoveriMD client

```conda install -c irl nanover-imd```

With this, the iMD-VR client is installed. Upon running the cell in jupyter notebook to create a session, you need to run:

```NanoverIMD```

this will display on your headset the app (You need to be LINKED to your computer either wired or wireless (AirLink)) and also on the computer

>[!IMPORTANT]
>To display it properly it is necessary to go inside the software Meta Quest Link, and set OpenXR Runtime as default for MetaQuest
>**Settings**➡️**General**➡️**OpenXR Runtime** 

*************************

## How to run Nanover apk with JupyterNotebook


>[!NOTE]
>First of all I will set some Keywords to explain this in a better way:
>- **PC**: Switch to PC
>- **MQ3**: Switch to Glasses
>
>From now on, I will give you some instructions and before the instruction I will put that keyword for you to know where we are each moment.



**MQ3 preparation:** 🕶️ 

1º Turn on the glasses.  
2º You must be connected to the same WiFi network as the PC.  
3º APK should be installed already. If not, check [For installing APK](#for-installing-apk) above.  


**PC preparation:** 🖥️

To run the files of Nanover, you need to download the repository from [GitHub](https://github.com/IRL2/nanover-server-py) to your computer:

- Code
- Download ZIP

1º Search on tool bar: **Anaconda Powershell Prompt** and open it  
2º run ```conda activate nanover```  
3º Navigate through and open the _nanover-server-py_ folder    
4º Inside **Anaconda Powershell Prompt** run:  
```python -m jupyterlab```  

This will open a new tab on your browser allowing you to use Jupyter and the files from Nanover.

### **PC**  
Once inside Jupyter you will be able to see the on the left the directories of the folder you are in.



