


def grabGun(motion_service, vertical_delta, horizontal_delta):
    # Arms motion from user have always the priority than walk arms motion

    JointNames = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw"]
    deg_to_rad = 0.017453
    # "RElbowRoll":5 metrów -  12 stopni. 3 metry - 14 stopni.
    # "RShoulderPitch" (bazowe): 5 metrów - -10 stopni. 3 metry - -8 stopni.
    arm_pos = [-20 - vertical_delta, -0.5, 14 + horizontal_delta, 0]
    arm_pos = [x * deg_to_rad for x in arm_pos]

    pFractionMaxSpeed = 0.5

    motion_service.angleInterpolationWithSpeed(JointNames, arm_pos, pFractionMaxSpeed)
    #motion_service.setAngles(JointNames, Arm1, pFractionMaxSpeed)
    #motion_service.setStiffnesses("RArm", 0.0)
    #motion_service.openHand("LHand")
    #motion_service.closeHand("LHand")

def lowerGun(motion_service):
    print("Lowering gun")
    joint_names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw"]
    deg_to_rad = 0.017453
    arm_pos = [90, 15, 0, 0]
    arm_pos = [x * deg_to_rad for x in arm_pos]
    max_speed_fraction = 0.5

    motion_service.angleInterpolationWithSpeed(joint_names, arm_pos, max_speed_fraction)

def moveFingers(motion_service):
    # Arms motion from user have always the priority than walk arms motion
    JointNames = ["LHand", "RHand", "LWristYaw", "RWristYaw"]
    deg_to_rad = 0.017453
    Arm1 = [0, 0, 0, 0]
    Arm1 = [x * deg_to_rad for x in Arm1]

    Arm2 = [50, 50, 0, 0]
    Arm2 = [x * deg_to_rad for x in Arm2]

    pFractionMaxSpeed = 0.8

    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm2, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)


def turnHead(motion_service, angle_degrees):
    """Turn head to specified angle in degrees"""
    JointNames = ["HeadYaw"]
    deg_to_rad = 0.017453
    Angles = [angle_degrees * deg_to_rad]
    
    pFractionMaxSpeed = 1.0
    # motion_service.wakeUp()
    motion_service.angleInterpolationWithSpeed(JointNames, Angles, pFractionMaxSpeed)
