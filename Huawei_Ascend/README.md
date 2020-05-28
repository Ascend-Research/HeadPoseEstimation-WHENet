# WHENet Head Pose Estimation \(Python\)<a name="EN-US_TOPIC_0232617557"></a>

## Project Overview

This project is a real-time video implementation of Wide Headpose Estimation Network(WHENet) on Atlas200DK board.

![](figures/whenet-output.png "whenet-output")

### Project Structure

![](figures/project-structure-final.png "project-structure")  

(Photo by: Randy Holmes/ABC)

## Application Deployment Steps

You can deploy this application on the Atlas 200 DK to collect camera data in real time and predict head information in the video.

The current application adapts to  [DDK&RunTime](https://ascend.huawei.com/resources)  of 1.3.0.0 as well as 1.32.0.0 and later versions.

### Prerequisites<a name="section1524472882216"></a>

Before deploying this sample, ensure that:

-   Mind Studio  has been installed.

-   The Atlas 200 DK developer board has been connected to  Mind Studio, the SD card has been created, and the build environment has been configured.
-   The developer board is connected to the Internet over the USB port by default. The IP address of the developer board is  **192.168.1.2**.

### Software Preparation<a name="section772075917223"></a>

Before running this application, obtain the source code package and configure the environment as follows.

1.  <a name="en-us_topic_0228757088_li953280133816"></a>Obtain the source code package.
    1.  By downloading the package

        Download all code in the repository at  [https://github.com/Atlas200dk-test/WHENetHeadPoseEstimation-python](https://github.com/Atlas200dk/WHENetHeadPoseEstimation-python)  to any directory on Ubuntu Server where  Mind Studio  is located as the  Mind Studio  installation user, for example,  **$HOME/WHENetHeadPoseEstimation-python**.

    2.  By running the  **git**  command

        Run the following command in the  **$HOME/AscendProjects**  directory to download code:

        **git clone https://github.com/Atlas200dk-test/WHENetHeadPoseEstimation-python.git**


2.  Log in to Ubuntu Server where  Mind Studio  is located as the  Mind Studio  installation user and set the environment variable  **DDK\_HOME**.

    **vim \~/.bashrc**

    1.  For the 1.3.0.0 version, run the following commands to append the end line with the environment variables  **DDK\_HOME**  and  **LD\_LIBRARY\_PATH**:

        **export DDK\_HOME=$HOME/tools/che/ddk/ddk**

        **export LD\_LIBRARY\_PATH=$DDK\_HOME/uihost/lib**

    2.  For 1.32.0.0 or later, run the following commands to append the environment variables:

        **export tools\_version=_1.32.X.X_**

        **export DDK\_HOME= $HOME/.mindstudio/huawei/ddk/$tools\_version/ddk**

        **export LD\_LIBRARY\_PATH= $DDK\_HOME/lib/x86\_64-linux-gcc5.4:$DDK\_HOME/uihost/lib**

        >![](public_sys-resources/icon-note.gif) **NOTE:**   
          >-   For 1.32.0.0 or later,  **1.32.X.X**  indicates the DDK version, which can be obtained from the DDK package name. For example, if the DDK package name is  **Ascend\_DDK-1.32.0.B080-1.1.1-x86\_64.ubuntu16.04.tar.gz**, the DDK version is  **1.32.0.B080**.  
          >-   If the environment variables have been added, skip this step.  

         Type  **:wq!**  to save settings and exit.

         Run the following command for the environment variable to take effect:

         **source \~/.bashrc**


### Environment Settings<a name="section1637464117139"></a>

Note: If the HiAI library, OpenCV library, and related dependencies have been installed on the developer board, skip this step.

1.  Configure the network connection of the developer board.

    Configure the network connection of the Atlas DK developer board by referring to  [https://github.com/Atlas200dk/sample-README/tree/master/DK\_NetworkConnect](https://github.com/Atlas200dk/sample-README/tree/master/DK_NetworkConnect).

2.  Install the environment dependencies（please deploy in python3）.

    Configure the environment dependency by referring to  [https://github.com/Atlas200dk/sample-README/tree/master/DK\_Environment](https://github.com/Atlas200dk/sample-README/tree/master/DK_Environment).


### Deployment<a name="section19787193103013"></a>

1.  Go to the root directory where the WHENetHeadPoseEstimation-python application code is located as the  Mind Studio  installation user, for example,  **$HOME/WHENetHeadPoseEstimation-python**.
2.  In  **whenet.conf**, change **presenter\_server\_ip** to the IP address of the ETH port on the Ubuntu server for connecting to the Atlas 200 DK developer board, and  **atlas200dk\_board\_ip** to the IP address of the ETH port on the developer board for connecting to the Ubuntu server.

    In USB connection mode, the IP address of the USB ETH port on the Atlas DK is 192.168.1.2, and the IP address of the virtual NIC ETH port on the Ubuntu server connected to the Atlas DK is 192.168.1.123. The configuration file content is as follows:

    **presenter\_server\_ip=192.168.1.123**

    **presneter\_server\_port=7006**

    **atlas200dk\_board\_id=192.168.1.2**

    >![](public_sys-resources/icon-note.gif) **NOTE:**   
    >-   Generally,  **atlas200dk\_board\_ip** indicates the IP address of the USB ETH port on the Atlas 200 developer board. The default value is 192.168.1.2. In ETH connection mode,  **atlas200dk\_board\_ip** indicates the IP address of the ETH port on the Atlas 200 developer board. The default value is 192.168.0.2.  

3.  Copy the application code to the developer board.

    Go to the root directory of the WHENet headpose estimation application \(python\) code as the  Mind Studio  installation user, for example,  **$HOME/WHENetHeadPoseEstimation-python**, and run the following command to copy the application code to the developer board:

    **scp -r ../WHENetHeadPoseEstimation-python/ HwHiAiUser@192.168.1.2:/home/HwHiAiUser/HIAI\_PROJECTS**

    Type the password of the developer board as prompted. The default password is **Mind@123**.

4.  Start Presenter Server.

    Run the following command to start the Presenter Server program of the WHENet head pose estimation \(Python\) application in the background:

    **bash run\_presenter\_server.sh &**

    Use the pop-up URL to log in to Presenter Server. The following figure indicates that Presenter Server is started successfully.

    **Figure  1**  Home page<a name="en-us_topic_0228757088_fig64391558352"></a>  
    ![](figures/home-page.png "home-page")

    The following figure shows the IP address used by Presenter Server and  Mind Studio  to communicate with the Atlas 200 DK.

    **Figure  2**  IP address example<a name="en-us_topic_0228757088_fig1881532172010"></a>  
    ![](figures/ip-address-example.png "ip-address-example")

    In the preceding figure:

    -   The IP address of the Atlas 200 DK developer board is  **192.168.1.2**  \(connected in USB mode\).
    -   The IP address used by Presenter Server to communicate with the Atlas 200 DK is in the same network segment as the IP address of the Atlas 200 DK on the UI Host server, for example,  **192.168.1.123**.
    -   The following describes how to access the IP address \(such as  **10.10.0.1**\) of Presenter Server using a browser. Because Presenter Server and  Mind Studio  are deployed on the same server, you can access  Mind Studio  through the browser using the same IP address.


### Run<a name="section1578813311309"></a>

1.  Log in to the host side as the  **HwHiAiUser**  user in SSH mode on Ubuntu Server where  Mind Studio  is located.

    **ssh HwHiAiUser@192.168.1.2**

    >![](public_sys-resources/icon-note.gif) **NOTE:**   
    >-   The following uses the USB connection mode as an example. In this case, the IP address is 192.168.1.2. Replace the IP address as required.  

2.  Go to the directory where the application code is stored as the  **HwHiAiUser**  user.

    **cd \~/HIAI\_PROJECTS/WHENetHeadPoseEstimation-python**

3.  Run the application.

    **python3 main.py**

    >![](public_sys-resources/icon-note.gif) **NOTE:**   
    >- You can press  **Ctrl**+**C**  to stop the application.  
    >- Currently this case only supports python3.

4.  Use the URL displayed upon the start of the Presenter Server service to log in to Presenter Server.

    Wait for Presenter Agent to transmit data to the server. Click  **Refresh**. When there is data, the icon in the  **Status**  column for the corresponding channel changes to green, as shown in  [Figure 3](#en-us_topic_0228757088_fig113691556202312).

    **Figure  3**  Presenter Server page<a name="en-us_topic_0228757088_fig113691556202312"></a>  
    ![](figures/presenter-server-page.png "presenter-server-page")

    >![](public_sys-resources/icon-note.gif) **NOTE:**   
    >-   The Presenter Server supports a maximum of 10 channels at the same time \(each  _presenter\_view\_app\_name_  parameter corresponds to a channel\).  
    >-   Due to hardware limitations, each channel supports a maximum frame rate of 20 fps. A lower frame rate is automatically used when the network bandwidth is low.  

5.  Click a link in the  **View Name**  column, for example,  **video**  in the preceding figure, and view the result.

## Project Layout
    WHENetHeadPoseEstimation-python
    ├── atlasutil                    # HIAI processing for camera, graph, dvpp, presenteragent
    │   ├── ai  
    │       ├── graph.py             # create graph 
    │   └── ... 
    ├── model                        # om models folder         
    │   ├── whenet.om         
    │   └── yolo_v3.om        
    ├── whenet                       # WHENet preprocessing, inferenece, postprocessing
    ├── yolov3                       # YOLO V3 preprocessing, inferenece, postprocessing
    ├── main.py                      # real video implementation with camera, PresenterSever
    ├── single_image.py              # script for single image testing
    └── ...    
