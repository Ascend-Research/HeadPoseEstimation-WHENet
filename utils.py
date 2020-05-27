import numpy as np
from math import cos, sin, pi
import math
import cv2
from scipy.spatial import Delaunay

def softmax(x):
    x -= np.max(x,axis=1, keepdims=True)
    a = np.exp(x)
    b = np.sum(np.exp(x), axis=1, keepdims=True)
    return a/b

def draw_axis(img, yaw, pitch, roll, tdx=None, tdy=None, size = 100):
    # Referenced from HopeNet https://github.com/natanielruiz/deep-head-pose
    pitch = pitch * np.pi / 180
    yaw = -(yaw * np.pi / 180)
    roll = roll * np.pi / 180

    if tdx != None and tdy != None:
        tdx = tdx
        tdy = tdy
    else:
        height, width = img.shape[:2]
        tdx = width / 2
        tdy = height / 2

    # X-Axis pointing to right. drawn in red
    x1 = size * (cos(yaw) * cos(roll)) + tdx
    y1 = size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + tdy

    # Y-Axis | drawn in green
    #        v
    x2 = size * (-cos(yaw) * sin(roll)) + tdx
    y2 = size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + tdy

    # Z-Axis (out of the screen) drawn in blue
    x3 = size * (sin(yaw)) + tdx
    y3 = size * (-cos(yaw) * sin(pitch)) + tdy

    cv2.line(img, (int(tdx), int(tdy)), (int(x1),int(y1)),(0,0,255),2)
    cv2.line(img, (int(tdx), int(tdy)), (int(x2),int(y2)),(0,255,0),2)
    cv2.line(img, (int(tdx), int(tdy)), (int(x3),int(y3)),(255,0,0),2)
    return img

def projectPoints(X, K, R, t, Kd):
    """ Projects points X (3xN) using camera intrinsics K (3x3),
    extrinsics (R,t) and distortion parameters Kd=[k1,k2,p1,p2,k3].

    Roughly, x = K*(R*X + t) + distortion

    See http://docs.opencv.org/2.4/doc/tutorials/calib3d/camera_calibration/camera_calibration.html
    or cv2.projectPoints
    """

    x = np.asarray(R * X + t)

    x[0:2, :] = x[0:2, :] / x[2, :]

    r = x[0, :] * x[0, :] + x[1, :] * x[1, :]

    x[0, :] = x[0, :] * (1 + Kd[0] * r + Kd[1] * r * r + Kd[4] * r * r * r) + 2 * Kd[2] * x[0, :] * x[1, :] + Kd[3] * (
                r + 2 * x[0, :] * x[0, :])
    x[1, :] = x[1, :] * (1 + Kd[0] * r + Kd[1] * r * r + Kd[4] * r * r * r) + 2 * Kd[3] * x[0, :] * x[1, :] + Kd[2] * (
                r + 2 * x[1, :] * x[1, :])

    x[0, :] = K[0, 0] * x[0, :] + K[0, 1] * x[1, :] + K[0, 2]
    x[1, :] = K[1, 0] * x[0, :] + K[1, 1] * x[1, :] + K[1, 2]

    return x

def align(model, data):
    """Align two trajectories using the method of Horn (closed-form).
    https://github.com/raulmur/evaluate_ate_scale

    Input:
    model -- first trajectory (3xn)
    data -- second trajectory (3xn)

    Output:
    rot -- rotation matrix (3x3)
    trans -- translation vector (3x1)
    trans_error -- translational error per point (1xn)

    """
    np.set_printoptions(precision=3, suppress=True)
    model_zerocentered = model - model.mean(1)
    data_zerocentered = data - data.mean(1)

    W = np.zeros((3, 3))
    for column in range(model.shape[1]):
        W += np.outer(model_zerocentered[:, column], data_zerocentered[:, column])
    U, d, Vh = np.linalg.linalg.svd(W.transpose())
    S = np.matrix(np.identity(3))
    if (np.linalg.det(U) * np.linalg.det(Vh) < 0):
        S[2, 2] = -1
    rot = U * S * Vh

    rotmodel = rot * model_zerocentered
    dots = 0.0
    norms = 0.0

    for column in range(data_zerocentered.shape[1]):
        dots += np.dot(data_zerocentered[:, column].transpose(), rotmodel[:, column])
        normi = np.linalg.norm(model_zerocentered[:, column])
        norms += normi * normi

    s = float(dots / norms)

    trans = data.mean(1) - s * rot * model.mean(1)

    model_aligned = s * rot * model + trans
    alignment_error = model_aligned - data

    trans_error = np.sqrt(np.sum(np.multiply(alignment_error, alignment_error), 0)).A[0]

    return rot, trans, trans_error, s

def rotationMatrixToEulerAngles2(R):
    y1 = -math.asin(R[2,0])
    y2 = math.pi - y1
    if y1>math.pi:
        y1 = y1 - 2*math.pi
    if y2>math.pi:
        y2 = y2 - 2*math.pi

    x1 = math.atan2(R[2,1]/math.cos(y1), R[2,2]/math.cos(y1))
    x2 = math.atan2(R[2,1]/math.cos(y2), R[2,2]/math.cos(y2))

    z1 = math.atan2(R[1,0]/math.cos(y1), R[0,0]/math.cos(y1))
    z2 = math.atan2(R[1, 0] / math.cos(y2), R[0, 0] / math.cos(y2))
    return [x1, y1, z1], [x2, y2, z2]

def reference_head(scale=0.01,pyr=(10.,0.0,0.0)):
    kps = np.asarray([[-7.308957, 0.913869, 0.000000], [-6.775290, -0.730814, -0.012799],
        [-5.665918, -3.286078, 1.022951], [-5.011779, -4.876396, 1.047961],
        [-4.056931, -5.947019, 1.636229], [-1.833492, -7.056977, 4.061275],
        [0.000000, -7.415691, 4.070434], [1.833492, -7.056977, 4.061275],
        [4.056931, -5.947019, 1.636229], [5.011779, -4.876396, 1.047961],
        [5.665918, -3.286078, 1.022951],
        [6.775290, -0.730814, -0.012799], [7.308957, 0.913869, 0.000000],
        [5.311432, 5.485328, 3.987654], [4.461908, 6.189018, 5.594410],
        [3.550622, 6.185143, 5.712299], [2.542231, 5.862829, 4.687939],
        [1.789930, 5.393625, 4.413414], [2.693583, 5.018237, 5.072837],
        [3.530191, 4.981603, 4.937805], [4.490323, 5.186498, 4.694397],
        [-5.311432, 5.485328, 3.987654], [-4.461908, 6.189018, 5.594410],
        [-3.550622, 6.185143, 5.712299], [-2.542231, 5.862829, 4.687939],
        [-1.789930, 5.393625, 4.413414], [-2.693583, 5.018237, 5.072837],
        [-3.530191, 4.981603, 4.937805], [-4.490323, 5.186498, 4.694397],
        [1.330353, 7.122144, 6.903745], [2.533424, 7.878085, 7.451034],
        [4.861131, 7.878672, 6.601275], [6.137002, 7.271266, 5.200823],
        [6.825897, 6.760612, 4.402142], [-1.330353, 7.122144, 6.903745],
        [-2.533424, 7.878085, 7.451034], [-4.861131, 7.878672, 6.601275],
        [-6.137002, 7.271266, 5.200823], [-6.825897, 6.760612, 4.402142],
        [-2.774015, -2.080775, 5.048531], [-0.509714, -1.571179, 6.566167],
        [0.000000, -1.646444, 6.704956], [0.509714, -1.571179, 6.566167],
        [2.774015, -2.080775, 5.048531], [0.589441, -2.958597, 6.109526],
        [0.000000, -3.116408, 6.097667], [-0.589441, -2.958597, 6.109526],
        [-0.981972, 4.554081, 6.301271], [-0.973987, 1.916389, 7.654050],
        [-2.005628, 1.409845, 6.165652], [-1.930245, 0.424351, 5.914376],
        [-0.746313, 0.348381, 6.263227], [0.000000, 0.000000, 6.763430],
        [0.746313, 0.348381, 6.263227], [1.930245, 0.424351, 5.914376],
        [2.005628, 1.409845, 6.165652], [0.973987, 1.916389, 7.654050],
        [0.981972, 4.554081, 6.301271]]).T
    R = rotate_zyx( np.deg2rad(pyr) )
    kps = transform( R, kps*scale )
    tris = Delaunay( kps[:2].T ).simplices.copy()
    return kps, tris

def rotate_zyx(theta):
    sx, sy, sz = np.sin(theta)
    cx, cy, cz = np.cos(theta)
    return np.array([
        [cy * cz, cy * sz, -sy, 0],
        [-cx * sz + cz * sx * sy, cx * cz + sx * sy * sz, cy * sx, 0],
        [cx * cz * sy + sx * sz, cx * sy * sz - cz * sx, cx * cy, 0],
        [0, 0, 0, 1]], dtype=float)

def transform( E, p ):
    p = np.array(p)
    if p.ndim > 1:
        return E[:3,:3]@p + E[:3,3,None]
    return E[:3,:3]@p + E[:3,3]

def get_sphere(theta, phi, row):
    theta = theta / 180. * pi
    phi = phi/ 180. * pi
    x = row * cos(theta) * sin(phi)
    y = row * sin(theta) * sin(phi)
    z = row * cos(phi)
    return x, y, z

def select_euler(two_sets):
    pitch, yaw,  roll= two_sets[0]
    pitch2, yaw2, roll2 = two_sets[1]
    if yaw>180.:
        yaw = yaw - 360.
    if yaw2>180.:
        yaw2 = yaw2 - 360.
    if abs(roll)<90 and abs(pitch)<90:
        return True, [pitch, yaw, roll]
    elif abs(roll2)<90 and abs(pitch2)<90:
        return True, [pitch2, yaw2, roll2]
    else:
        return False, [-999, -999, -999]

def inverse_rotate_zyx(M):
    if np.linalg.norm(M[:3, :3].T @ M[:3, :3] - np.eye(3)) > 1e-5:
        raise ValueError('Matrix is not a rotation')

    if np.abs(M[0, 2]) > 0.9999999:
        # gimbal lock
        z = 0.0
        # M[1,0] =  cz*sx*sy
        # M[2,0] =  cx*cz*sy
        if M[0, 2] > 0:
            y = -np.pi / 2
            x = np.arctan2(-M[1, 0], -M[2, 0])
        else:
            y = np.pi / 2
            x = np.arctan2(M[1, 0], M[2, 0])
        return np.array((x, y, z)), np.array((x, y, z))
    else:
        # no gimbal lock
        y0 = np.arcsin(-M[0, 2])
        y1 = np.pi - y0
        cy0 = np.cos(y0)
        cy1 = np.cos(y1)

        x0 = np.arctan2(M[1, 2] / cy0, M[2, 2] / cy0)
        x1 = np.arctan2(M[1, 2] / cy1, M[2, 2] / cy1)

        z0 = np.arctan2(M[0, 1] / cy0, M[0, 0] / cy0)
        z1 = np.arctan2(M[0, 1] / cy1, M[0, 0] / cy1)
        return np.array((x0, y0, z0)), np.array((x1, y1, z1))
