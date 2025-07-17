


def grabGun(motion_service):
    # Arms motion from user have always the priority than walk arms motion
    JointNames = ["RShoulderPitch", "RElbowRoll", "RWristYaw", "RHand"]
    deg_to_rad = 0.017453
    Arm1 = [45, 45, 0, 20]
    Arm1 = [x * deg_to_rad for x in Arm1]
    Arm2 = [50, 50, 0, 0]
    Arm2 = [x * deg_to_rad for x in Arm2]

    pFractionMaxSpeed = 1.0

    #motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm2, pFractionMaxSpeed)
    #motion_service.setAngles(JointNames, Arm1, pFractionMaxSpeed)
    #motion_service.setStiffnesses("RArm", 0.0)
    #motion_service.setStiffnesses("RHand", 0.0)
    motion_service.openHand("RHand")
    motion_service.closeHand("RHand")


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


def lookForward(motion_service):
    # Arms motion from user have always the priority than walk arms motion
    JointNames = ["HeadYaw", "HeadPitch"]
    deg_to_rad = 0.017453
    Angles = [0, 0]
    Angles = [x * deg_to_rad for x in Angles]

    pFractionMaxSpeed = 0.8
    # motion_service.setStiffnesses("Head", 1.0)
    # time.sleep(0.5)
    motion_service.wakeUp()
    motion_service.angleInterpolationWithSpeed(JointNames, Angles, pFractionMaxSpeed)
    #motion_service.setStiffnesses("Head", 0.0)


def turnHead(motion_service, angle_degrees):
    """Turn head to specified angle in degrees"""
    JointNames = ["HeadYaw"]
    deg_to_rad = 0.017453
    Angles = [angle_degrees * deg_to_rad]
    
    pFractionMaxSpeed = 1.0
    # motion_service.wakeUp()
    motion_service.angleInterpolationWithSpeed(JointNames, Angles, pFractionMaxSpeed)
