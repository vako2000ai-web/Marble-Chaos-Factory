"""Generate Marble Chaos Factory prototype in Blender background mode.

Usage:
 blender --background --python blender/scripts/generate_scene.py -- \
   --config config/scenes/prototype_01.json --out data/prototype_01.blend
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(name, rgba, metallic=0.0, roughness=0.25):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgba, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgba, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def cube(name, location, scale, mat, rigid=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if rigid:
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = "PASSIVE"
        obj.rigid_body.collision_shape = "BOX"
        obj.rigid_body.friction = 0.4
    return obj


def camera_at(location, target):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 11
    bpy.context.scene.camera = cam


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    n = int(cfg["ball_count"])
    radius = float(cfg["ball_radius"])
    if not 1 <= n <= 5000 or not 0.02 <= radius <= 0.2:
        raise ValueError("ball_count or ball_radius outside prototype limits")
    random.seed(int(cfg["seed"]))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.frame_end = int(cfg["frame_end"])
    scene.render.fps = int(cfg["fps"])
    scene.gravity = (0, 0, float(cfg.get("gravity", -9.81)))
    scene.render.engine = "CYCLES"
    scene.cycles.samples = int(cfg["render"]["samples"])
    scene.render.resolution_x = int(cfg["render"]["width"])
    scene.render.resolution_y = int(cfg["render"]["height"])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = "//frames/"

    chrome = material("Satin Chrome", (0.33, 0.48, 0.56), metallic=0.8)
    dark = material("Dark Factory", (0.018, 0.038, 0.065), metallic=0.45)
    palette = [material(name, rgb, metallic=0.15, roughness=0.16) for name, rgb in [
        ("Red", (0.95, 0.09, 0.14)), ("Blue", (0.05, 0.38, 0.94)),
        ("Green", (0.09, 0.8, 0.34)), ("Yellow", (1, 0.7, 0.04))
    ]]
    cube("Floor", (0, 0, -0.25), (12, 9, .4), dark, True)
    # Four individual inclined lanes, open on top, terminating above a collector.
    for lane in range(4):
        y = (lane - 1.5) * 1.10
        track = cube(f"Lane_{lane}", (0, y, 2.9), (5.2, .85, .12), chrome, True)
        track.rotation_euler[1] = math.radians(16)
        # Rigid-body transforms must be in sync with current frame before baking.
        for side in (-1, 1):
            wall = cube(f"Rail_{lane}_{side}", (0, y + side*.47, 3.13),
                        (5.3, .08, .45), chrome, True)
            wall.rotation_euler[1] = math.radians(16)
        cube(f"Collector_{lane}", (3.1, y, .6), (1.5, .98, .12), chrome, True)
        for i in range(n // 4 + (lane < n % 4)):
            # Grid packing for no initial overlaps; each lane gets a stream.
            col, row = i % 4, i // 4
            x = -2.25 + col * radius * 2.5
            z = 4.5 + row * radius * 2.55
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius, location=(x, y, z))
            marble = bpy.context.object
            marble.name = f"Marble_{lane}_{i:04d}"
            marble.data.materials.append(palette[lane])
            bpy.ops.rigidbody.object_add()
            marble.rigid_body.type = "ACTIVE"
            marble.rigid_body.collision_shape = "SPHERE"
            marble.rigid_body.mass = 0.05
            marble.rigid_body.restitution = 0.4
            marble.rigid_body.friction = 0.35
    camera_at((10, -12, 10), (0, 0, 2))
    bpy.ops.object.light_add(type="AREA", location=(1, -3, 10))
    bpy.context.object.data.energy = 3000
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 9
    scene.world.color = (.10, .10, .10)
    if scene.rigidbody_world:
        scene.rigidbody_world.substeps_per_frame = 60
        scene.rigidbody_world.solver_iterations = 20
        scene.rigidbody_world.point_cache.frame_end = scene.frame_end
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Created {output} with {n} marbles")


if __name__ == "__main__":
    main()
