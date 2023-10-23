import numpy as np
import cv2
import rospy
from cv_bridge import CvBridge
from std_msgs.msg import Boolean

cv_bridge = CvBridge()

PYDEVD_DISABLE_FILE_VALIDATION=1
STOPPING_DISTANCE = 100 #mm
MAXIMUM_DISTANCE = 50000 #mm
MINIMUM_DISTANCE = 1 #mm
MINAREA = 800 #pixels
CAMERA_VFOV=54 #degrees
CAMERA_VRES = 720 #pixels
CAMERA_HEIGHT = 100 #mm

def depth_callback(data):
    mat = cv_bridge.imgmsg_to_cv2(data, desired_encoding = 'passthrough')
    depth_nparr = np.array(mat, dtype=np.float32)
    depth_masked = depthmask(depth_nparr)
    pub.publish(determine_stop(depth_masked))
    rate.sleep()

def runrun():
    rospy.init_node('AEB_sender', anonymous=True)
    pub = rospy.Publisher('AEB', Boolean, queue_size=1)
    depthsub = rospy.Subscriber("/zed/zed_node/depth/depth_registered", Image, depth_callback, 1)
    r = rospy.Rate(10)

def depthmask(nparr):
    nanless = np.nan_to_num(nparr)
    nanless[nanless == 0] = MAXIMUM_DISTANCE
    return nanless

def determine_stop(arr):
    nparr = np.array(arr)
    degree_change_pp = (CAMERA_VFOV)/(CAMERA_VRES)

    for i in range(1, len(nparr)+1):
        if i < len(nparr)//2:
            road_filter = np.logical_and(nparr[len(nparr)-i ] < (CAMERA_HEIGHT * np.tan((90 - CAMERA_VFOV/2 + degree_change_pp*i)*np.pi/180)) , nparr[len(nparr)-i ] < STOPPING_DISTANCE)
            road_filter = road_filter*1 #normalizes to ints
            nparr[len(nparr) - i] = road_filter 
        else:
            road_filter = nparr[len(nparr)-i] < STOPPING_DISTANCE
            road_filter = road_filter*1
            nparr[len(nparr) - i] = road_filter
    
    nparr = nparr.astype(np.uint8)
    kernel = np.ones((30,30), np.uint8)
    cv2.erode(nparr, kernel)
    cv2.dilate(nparr,kernel)
    contours, dummy = cv2.findContours(nparr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    nparr = nparr * 255

    if len(contours) == 0:
        return False
    else:
        for cnt in contours:
            if cv2.contourArea(cnt) >= MINAREA:
                return True
        return False

if __name__ == '__Main__':
    runrun()

