# MIT License

# Copyright (c) 2023 Thomas van den Berg

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

bl_info = {
    "name": "Pixel Unwrapper",
    "author": "Thomas 'noio' van den Berg",
    "description": "",
    "blender": (4, 3, 0),
    "version": (0, 5, 0),
    "location": "",
    "warning": "",
    "category": "Generic",
}

import bpy
from . import auto_load

auto_load.init()


def _update_object_grid_density(self, context):
    if self.pixunwrap_grid_mode == "OBJECT" and self.pixunwrap_ref_edge_length > 1e-6:
        self.pixunwrap_texel_density = self.pixunwrap_ref_edge_pixels / self.pixunwrap_ref_edge_length


def _update_texel_density(self, context):
    density = self.pixunwrap_texel_density
    if density <= 0:
        return
    pixel_size = 1.0 / density
    try:
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.overlay.grid_scale = pixel_size
                        space.overlay.grid_subdivisions = 1
    except Exception:
        pass


def _update_live_unwrap(self, context):
    """Initialize face geometry snapshot when Live Unwrap is activated"""
    if self.pixunwrap_live_unwrap:
        obj = context.active_object
        if obj and obj.type == "MESH" and obj.mode == "EDIT":
            try:
                from .operators import _live_unwrap_face_geometry, _get_all_faces_geometry
                import bmesh
                bm = bmesh.from_edit_mesh(obj.data)
                _live_unwrap_face_geometry[obj.name] = _get_all_faces_geometry(bm)
            except Exception:
                pass


@bpy.app.handlers.persistent
def _apply_pixel_snap_handler(dummy):
    try:
        for scene in bpy.data.scenes:
            try:
                scene.tool_settings.use_snap_uv_grid_absolute = True
            except AttributeError:
                pass
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "IMAGE_EDITOR":
                    for space in area.spaces:
                        if space.type == "IMAGE_EDITOR":
                            try:
                                space.pixel_snap_mode = "CORNER"
                            except AttributeError:
                                pass
    except Exception:
        pass


def register():
    auto_load.register()

    bpy.types.Scene.pixunwrap_texel_density = bpy.props.FloatProperty(
        name="Pixels Per Unit",
        default=16,
        description="",
        update=_update_texel_density,
    )

    bpy.types.Scene.pixunwrap_grid_mode = bpy.props.EnumProperty(
        name="Grid Mode",
        default="WORLD",
        description="How the pixel density is defined",
        items=[
            ("WORLD", "World Grid", "Pixels Per Unit based on Blender world units"),
            ("OBJECT", "Object Grid", "Pixels Per Unit derived from a reference edge of the object"),
        ],
    )

    bpy.types.Scene.pixunwrap_ref_edge_length = bpy.props.FloatProperty(
        name="Reference Edge Length",
        default=1.0,
        min=0.0001,
        precision=4,
        description="World-space length of the reference edge (set via 'Set Reference Edge')",
    )

    bpy.types.Scene.pixunwrap_ref_edge_pixels = bpy.props.IntProperty(
        name="Pixels",
        default=8,
        min=1,
        max=4096,
        description="How many pixels the reference edge spans in the texture",
        update=_update_object_grid_density,
    )

    bpy.types.Scene.pixunwrap_default_texture_size = bpy.props.IntProperty(
        name="Default Texture Size",
        default=64,
        description="This is also used when unwrapping objects that have no texture assigned",
    )

    bpy.types.Scene.pixunwrap_texture_fill_color_tl = bpy.props.FloatVectorProperty(
        name="Texture Fill A",
        default=[0.92, 0.69, 0.69],
        description="Color used to fill top left quadrant of empty texture",
        subtype="COLOR",
        min=0,
        max=1
    )
    bpy.types.Scene.pixunwrap_texture_fill_color_bl = bpy.props.FloatVectorProperty(
        name="Texture Fill B",
        default=[0.72, 0.72, 0.84],
        description="Color used to fill bottom left quadrant of empty texture",
        subtype="COLOR",
        min=0,
        max=1
    )

    bpy.types.Scene.pixunwrap_texture_fill_color_tr = bpy.props.FloatVectorProperty(
        name="Texture Fill C",
        default=[0.64, 0.91, 0.64],
        description="Color used to fill top right quadrant of empty texture",
        subtype="COLOR",
        min=0,
        max=1
    )
    # YELLOW
    bpy.types.Scene.pixunwrap_texture_fill_color_br = bpy.props.FloatVectorProperty(
        name="Texture Fill D",
        default=[1, 0.79, 0.48],
        description="Color used to fill bottom right quadrant of empty texture",
        subtype="COLOR",
        min=0,
        max=1
    )

    uv_behaviors = (
        ("DESTRUCTIVE", "Destructive", ""),
        ("PRESERVE", "Preserve Texture", ""),
    )

    bpy.types.Scene.pixunwrap_uv_behavior = bpy.props.EnumProperty(
        name="UV Change Behavior",
        default=0,
        description="When using UV operators, should the image be modified to preserve texturing",
        items=uv_behaviors,
    )

    bpy.types.Scene.pixunwrap_modify_texture = bpy.props.BoolProperty(
        name="Modify Texture",
        default=False,
        description="Should the texture be modified to keep painted pixels in place on the model, or can UV's be moved freely.",
    )

    bpy.types.Scene.pixunwrap_fold_sections = bpy.props.IntProperty(
        name="Fold Sections",
        default=2,
        description="How many sections to fold the selected UV grid into.",
    )

    bpy.types.Scene.pixunwrap_fold_alternate = bpy.props.BoolProperty(
        name="Fold Alternate",
        default=False,
        description="Alternate directions of folded sections in a zig-zag way. Turn off to cut and stack sections",
    )

    bpy.types.Scene.pixunwrap_live_unwrap = bpy.props.BoolProperty(
        name="Live Grid Unwrap",
        default=False,
        description="Automatically re-run Grid Unwrap when vertex positions change in Edit Mode",
        update=_update_live_unwrap,
    )

    from .operators import live_unwrap_depsgraph_handler
    if live_unwrap_depsgraph_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(live_unwrap_depsgraph_handler)

    if _apply_pixel_snap_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_apply_pixel_snap_handler)
    if _apply_pixel_snap_handler not in bpy.app.handlers.load_factory_startup_post:
        bpy.app.handlers.load_factory_startup_post.append(_apply_pixel_snap_handler)


def unregister():
    from .operators import live_unwrap_depsgraph_handler

    if live_unwrap_depsgraph_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(live_unwrap_depsgraph_handler)

    if _apply_pixel_snap_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_apply_pixel_snap_handler)
    if _apply_pixel_snap_handler in bpy.app.handlers.load_factory_startup_post:
        bpy.app.handlers.load_factory_startup_post.remove(_apply_pixel_snap_handler)

    auto_load.unregister()
