import bpy
import numpy as np
import math
from math import pi as PI
import random
import time
from mathutils import Euler, Color
from pathlib import Path
import random
from mathutils import Vector
import os

def randomly_rotate_object(obj_to_change):
    
    """
    Applies a rnadom rotation to an object
    
    """
    
    random_rot = (random.random() * 2 * math.pi,
                    random.random() * 2 * math.pi,
                    random.random() * 2 * math.pi)
    obj_to_change.rotation_euler = Euler(random_rot, 'XYZ')
    
def randomly_change_color(material_to_change):
    """
    Changes the principled BSDF color of a material to a random color
    """
    color = Color()
    hue = random.random()
    color.hsv = (hue,1,1)
    rgba = [color.r, color.g, color.b, 1]
    material_to_change.node_tree.nodes['Principled BSDF'].inputs[0].default_value = rgba
    
def randomly_set_camera_position():
    # Set the circular path position (0 to 100)
    bpy.context.scene.objects['CameraContainer'].constraints['Follow Path'].offset = random.random() * 100
    
    # Set the arc path position (0 to 100, not sure why, to be honest)
    bpy.context.scene.objects['CirclePathContainer'].constraints['Follow Path'].offset = random.random() * -100


def generate_letter_dataset(num_train, num_val, num_test):
    # Object names to render
    obj_names = ['A','B','C']
    obj_count = len(obj_names)

    # Number of images to generate of each object for each split of the dataset
    # Example: ('train',100) means generate 100 imagbes of each of 'A', 'B', & 'C' resulting in 300 training images
    obj_renders_per_split = [('train',num_train),('val',num_val),('test',num_test)]

    # Output path
    output_path = Path("/Users/billymazotti/github/blender_shenanigans/DatasetGeneration/abc_test")

    # For each dataset split (train/val/test), multiply the number of renders per object by
    # the number of objects (3, since we ahve A, B, and C). Then compute the sum.
    # This will be the total number of renders performed.
    total_render_count = sum([obj_count * r[1] for r in obj_renders_per_split])

    # Set all objecrts to be hidden in rendering
    for name in obj_names:
        bpy.context.scene.objects[name].hide_render = True
        
    # Tracks the starting image index for each object loop
    start_idx = 0

    # Keep trakc of start time (in seconds)
    start_time = time.time()

    # Loop through each split of the dataset
    for split_name, renders_per_object in obj_renders_per_split:
        print(f'Starting split: {split_name} | Total renders: {renders_per_object * obj_count}')
        print("=============================")
        
        # Loop through the objects by name
        for obj_name in obj_names:
            print(f'Starting object: {split_name}/{obj_name}')
            print('..........................')
            
            
            # Get the next object and make it visible
            obj_to_render = bpy.context.scene.objects[obj_name]
            obj_to_render.hide_render = False
            
            # Loop through all image renders for this object
            for i in range(start_idx, start_idx + renders_per_object):
                # Change the object
                randomly_rotate_object(obj_to_render)
                randomly_change_color(obj_to_render.material_slots[0].material)
                
                # Log status
                print(f'Rendering image {i + 1} or {total_render_count}')
                seconds_per_render = (time.time() - start_time) / (i + 1)
                seconds_remaining = seconds_per_render * (total_render_count - i - 1)
                print(f'Estimated time remaining: {time.strftime("%H:%M:%S", time.gmtime(seconds_remaining))}')
                
                # Update file path and render
                bpy.context.scene.render.filepath = str(output_path / split_name / obj_name / f'{str(i).zfill(6)}.png')
                bpy.ops.render.render(write_still=True)
                
            # Hide the object, we're done with it
            obj_to_render.hide_render = True
                
            
            # update the starting image index
            start_idx += renders_per_object

    print(f'Total Generation time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))}')



    # Set all objects to be visible in rendering
    for name in obj_names:
        bpy.context.scene.objects[name].hide_render = False
        
        
def positionCamera(x_pos, y_pos, z_pos, roll_deg):
    """
    Moves the CameraTarget Object 
    """
#    bpy.data.objects["Camera"].select_set(True)
#    current_state = bpy.data.objects["Camera"].select_get()
    bpy.context.view_layer.objects.active = bpy.data.objects['Camera']

    # position camera to specified x,y,z location
    bpy.data.objects["Camera"].location = [x_pos, y_pos, z_pos]
    
    # set specific axis to point up
    bpy.ops.object.constraint_add(type='TRACK_TO')
#    bpy.context.object.constraints["Track To"].target = bpy.data.objects["CameraTarget"]
#    bpy.context.object.constraints["Track To"].up_axis = 'UP_Y'
    bpy.data.objects["Camera"].constraints["Track To"].target = bpy.data.objects["CameraTarget"]
    bpy.data.objects["Camera"].constraints["Track To"].up_axis = 'UP_Y'
    bpy.ops.constraint.apply(constraint="Track To", owner='OBJECT')

    # save the upright angle
    upright_camera_orientation = bpy.data.objects["Camera"].rotation_euler
    bpy.context.scene.transform_orientation_slots[0].type = 'GLOBAL'
    upright_camera_orientation = bpy.data.objects["Camera"].rotation_euler
    
    # delete TRACK_TO constraint to allow for camera roll
    bpy.ops.constraint.delete(constraint="Track To", owner='OBJECT')
    bpy.data.objects["Camera"].rotation_euler = upright_camera_orientation
    
    # add roll to camera
    bpy.data.objects["Camera"].rotation_mode = 'ZYX'
    bpy.data.objects["Camera"].rotation_euler[2] = upright_camera_orientation[2] + \
                                                        roll_deg*PI/180



def placeCameraInVolume(cubeMeshName,roll):
    """
    randomly place camera in an UNROTATED mesh cube primitive
    
    cube primite cannot be rotated, only changed in scale and location
    """
    
    # define the x,y,z limits of the cube mesh
    centroidXYZ = np.array(bpy.data.objects[cubeMeshName].location)
    dimensionsXYZ = np.array(bpy.data.objects[cubeMeshName].dimensions)
    camera_volume_limits = centroidXYZ * np.ones((2,3))
    camera_volume_limits[0,:] -= dimensionsXYZ/2
    camera_volume_limits[1,:] += dimensionsXYZ/2

    camera_volume_limits_mm = (camera_volume_limits * 1000).astype(int)

    # genrate random x,y,z point within the volume for camera placement
    randX = random.randrange(start = camera_volume_limits_mm[0,0],
                            stop = camera_volume_limits_mm[1,0],
                            step = 1) / 1000
    randY = random.randrange(start = camera_volume_limits_mm[0,1],
                            stop = camera_volume_limits_mm[1,1],
                            step = 1) / 1000
    randZ = random.randrange(start = camera_volume_limits_mm[0,2],
                            stop = camera_volume_limits_mm[1,2],
                            step = 1) / 1000
    
    positionCamera(randX, randY, randZ, roll)
    

def placeObjectOnPlane(planeName, objectName, objects_dict):
    """
        assmes object is small enough to fit in plane
        assumes object has local z vecotr pointing up 
        
        current errors:
            - roll grows exponentially
            
    """
    
    # set position to ensure object is not hanging off plane
    
    # define the x,y limits of the plane
    centroidXYZ = np.array(bpy.data.objects[planeName].location)
    planeDimensionsXYZ = np.array(bpy.data.objects[planeName].dimensions)
    objectDimensionsXYZ = np.array(bpy.data.objects[objectName].dimensions)
   
    max_object_length = max(objectDimensionsXYZ[0],objectDimensionsXYZ[1])
    
    object_plane_limits = centroidXYZ[0:2] * np.ones((2,2))
    object_plane_limits[0,:] -= (planeDimensionsXYZ[0:2] - max_object_length)/2
    object_plane_limits[1,:] += (planeDimensionsXYZ[0:2] - max_object_length)/2
    
    object_plane_limits_mm = (object_plane_limits * 1000).astype(int)
    
    # genrate random x,y,z point within the volume for camera placement
    randX = random.randrange(start = object_plane_limits_mm[0,0],
                            stop = object_plane_limits_mm[1,0],
                            step = 1) / 1000
    randY = random.randrange(start = object_plane_limits_mm[0,1],
                            stop = object_plane_limits_mm[1,1],
                            step = 1) / 1000
    z_pos = centroidXYZ[2]                    
#    positionObject()
    
    
    bpy.data.objects[objectName].location = [randX, randY, z_pos]
    
    # set orientation
    if (objects_dict[objectName]["rot_limits"][0,1] - \
            objects_dict[objectName]["rot_limits"][0,0] == 0):
        randX_theta = objects_dict[objectName]["rot_limits"][0,0]
    else:
        randX_theta = random.randrange(start = objects_dict[objectName]["rot_limits"][0,0],
                                        stop = objects_dict[objectName]["rot_limits"][0,1],
                                        step = 1)
    if (objects_dict[objectName]["rot_limits"][1,1] - \
            objects_dict[objectName]["rot_limits"][1,0] == 0):
        randY_theta = objects_dict[objectName]["rot_limits"][0,0]
    else:
        randY_theta = random.randrange(start = objects_dict[objectName]["rot_limits"][1,0],
                                        stop = objects_dict[objectName]["rot_limits"][1,1],
                                        step = 1)
    if (objects_dict[objectName]["rot_limits"][2,1] - \
            objects_dict[objectName]["rot_limits"][2,0] == 0):
        randZ_theta = objects_dict[objectName]["rot_limits"][0,0]
    else:
        randZ_theta = random.randrange(start = objects_dict[objectName]["rot_limits"][2,0],
                                        stop = objects_dict[objectName]["rot_limits"][2,1],
                                        step = 1)
                                        
    bpy.data.objects[objectName].rotation_euler = [randX_theta,randY_theta,randZ_theta]

def objects_in_fov():
    """
    Retern a list of all coco object names
    output:

    """
    
    camera = bpy.context.scene.camera
    fov = camera.data.angle
    location = camera.location
    direction = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    visible_objects = [obj for obj in bpy.context.scene.objects if not obj.hide_render]

    # creeat list of all visible objects in fob
    objects_in_fov = []
    for obj in visible_objects:
        if obj.type != 'MESH' or not obj.visible_get(): 
            continue    # skip non mesh and non-visible objects
        if obj.name.split("_")[0] != 'obj':
            continue    # skip objects that don't start with obj_
        for v in obj.data.vertices:
            vertex_world = obj.matrix_world @ v.co
            to_vertex = vertex_world - location
            angle_to_vertex = direction.angle(to_vertex)
            if angle_to_vertex < fov / 2:
                objects_in_fov.append(obj.name)
                break
            
    objects_in_fov.sort()
    return objects_in_fov
    

def annotate_2Dand_3D_data_of_in_view_objects():
    """
    Determine which objects are in view and are showing at least X pixels? in FOV?
    - Step 1: find all objects in fov using fov script (still could be occluded)
    - Step 2: create mask of each object in FOV and if there's at least 1 pixel then annotate the object
        https://www.youtube.com/watch?v=xeprI8hJAH8
    - Step 3: get the object's distance from the camera using object's centroid location 
        (make sure this is the actual centroid and not just the object's groudnign point) xyz data
    """
    
    
    # retreive objects in the field of view
    object_in_fov_names = objects_in_fov()
    
    # assign pass_idx to all subassembly parts
    min_pass_idx = 1
    
    previous_obj = object_in_fov_names[0]
    for obj in object_in_fov_names:
        if previous_obj.split("_")[0:5] == obj.split("_")[0:5]:
            bpy.data.objects[obj].pass_index = min_pass_idx
        else:
            min_pass_idx += 1
            bpy.data.objects[obj].pass_index = min_pass_idx
        previous_obj = obj
        
        print(obj)
        print(bpy.data.objects[obj].pass_index)
        
    

def spawn_object_with_geofence():
    """
    Priority Number 2
    
    Methods
    - use occupancy grid with footprints
    - give max number of new attemps and check for collisions
    """
    
    None
    


# roation limits = np.array([[min_x,max_x],[min_y,max_y],[min_z,max_y]])
# objects_dict = {}
# objects_dict["obj_pepsi_up"] = {}
# objects_dict["obj_pepsi_up"]["rot_limits"] = np.array([[0,0],[0,0],[0,360]])
# objects_dict["obj_pepsi_side"] = {}
# objects_dict["obj_pepsi_side"]["rot_limits"] = np.array([[0,0],[0,0],[0,360]])
                            
# placeObjectOnPlane("Object Plane", "obj_pepsi_up", objects_dict)  
# placeObjectOnPlane("Object Plane", "obj_pepsi_side", objects_dict)   

placeCameraInVolume("CameraVolume",roll=0)




# RENDER SETTINGS
RENDER = True
bpy.data.scenes["Scene"].cycles.samples = 10

if RENDER:
    num_enviornmetns = 1
    start_idx = 0
    renders_per_environment = 10
    start_time = time.time()

    total_render_count = num_enviornmetns * renders_per_environment

    renter_rates = np.zeros(total_render_count)

    print("STARTING DATASET GENERATION...")
    for i in range(start_idx, start_idx + renders_per_environment):
        
        # randomly place camera in a volume defined by a cube mesh
        placeCameraInVolume("CameraVolume",roll=0)
        
        # randomly place objects on plane defined by a plane mesh
        # TODO
        
        
        # set pass index for all objects to 0
        for obj in bpy.data.objects:
            bpy.data.objects[obj.name].pass_index = 0

        annotate_2Dand_3D_data_of_in_view_objects()

        # render image
        bpy.context.scene.render.filepath =  os.getcwd() + f"/data/images/{str(i).zfill(6)}.png"
        bpy.ops.render.render(write_still=True)
        
        # save sementation image
        os.rename(os.getcwd() + "/data/Segmentation0116.png", os.getcwd() + f"/data/masks/{str(i).zfill(6)}.png")
        
        # render rate statistics
        renter_rates[i] =  (time.time() - start_time) / (i + 1)
        seconds_remaining = renter_rates[i] * (total_render_count - i - 1)
        print(f'\nRemaining Time: {time.strftime("%H:%M:%S",time.gmtime(seconds_remaining))}s')
        print(f'Current | Avg | Max | Min Renter Rates (s/img): {round(renter_rates[i],2)} | {round(renter_rates[:i+1].mean(),2)} | {round(renter_rates[:i+1].max(),2)} | {round(renter_rates[:i+1].min(),2)}')

    print("DATASET GENERATION COMPLETE!")

# print("\nhello there\n")

                    


    
    
        
