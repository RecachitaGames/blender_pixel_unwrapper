import bpy
from .operators import *

from .common import get_first_texture_on_object


def _draw_texture_setup(self, context):
    layout = self.layout
    scene = context.scene

    has_texture = (
        context.view_layer.objects.active is not None
        and get_first_texture_on_object(context.view_layer.objects.active) is not None
    )

    col = layout.column()

    row = col.row(align=True)
    row.operator("view3d.pixunwrap_create_texture", text="Create New")
    row.operator("view3d.pixunwrap_duplicate_texture", text="Duplicate")

    col.separator(factor=0.5)

    row = col.row(align=True)
    row.prop(scene, "pixunwrap_grid_mode", expand=True)

    if scene.pixunwrap_grid_mode == "WORLD":
        row = col.row(align=True)
        row.prop(scene, "pixunwrap_texel_density")
        row.operator("view3d.pixunwrap_set_density_from_edge", text="", icon="EDGESEL")
    else:
        if scene.pixunwrap_ref_edge_length > 1e-6:
            derived = scene.pixunwrap_ref_edge_pixels / scene.pixunwrap_ref_edge_length
            subcol = col.column(align=True)
            row = subcol.row(align=True)
            row.label(text=f"Edge: {scene.pixunwrap_ref_edge_length:.4f} u  =")
            row.prop(scene, "pixunwrap_ref_edge_pixels", text="px")
            subcol.label(text=f"→  {derived:.2f} px / unit", icon="INFO")
        else:
            col.label(text="No reference edge set yet", icon="ERROR")
        col.operator("view3d.pixunwrap_set_reference_edge", icon="EDGESEL")

    col.prop(scene, "pixunwrap_default_texture_size", text="Fallback Texture Size")

    row = col.row(align=True)
    row.enabled = has_texture
    op = row.operator("view3d.pixunwrap_resize_texture", text="Double (×2)")
    op.scale = 2
    op = row.operator("view3d.pixunwrap_resize_texture", text="Halve (÷2)")
    op.scale = 0.5

    col.label(text="Fill Colors")
    row = col.row(align=True)
    row.prop(scene, "pixunwrap_texture_fill_color_tl", text="")
    row.prop(scene, "pixunwrap_texture_fill_color_tr", text="")
    row.prop(scene, "pixunwrap_texture_fill_color_bl", text="")
    row.prop(scene, "pixunwrap_texture_fill_color_br", text="")


def _draw_unwrapping(self, context):
    layout = self.layout
    scene = context.scene

    if not scene.tool_settings.use_uv_select_sync:
        row = layout.row()
        row.alert = True
        row.label(text='"UV Sync Selection" must be enabled', icon="ERROR")

    col = layout.column(align=True)
    col.scale_y = 1.5
    col.operator("view3d.pixunwrap_unwrap_grid", icon="OUTLINER_OB_LATTICE")
    col.operator("view3d.pixunwrap_unwrap_basic", icon="SELECT_SET")
    col.operator(PIXUNWRAP_OT_unwrap_single_pixel.bl_idname)

    col = layout.column(align=False)
    col.scale_y = 1.5
    col.operator("view3d.pixunwrap_hotspot", icon="MOD_UVPROJECT")

    layout.prop(scene, "pixunwrap_live_unwrap", icon="FILE_REFRESH")


def _draw_uv_editing(self, context):
    layout = self.layout
    scene = context.scene
    modify_texture = scene.pixunwrap_modify_texture

    row = layout.row()
    row.scale_y = 1.4
    row.prop(scene, "pixunwrap_modify_texture", icon="ERROR")

    col = layout.column(align=True)
    col.enabled = not modify_texture
    col.operator("view3d.pixunwrap_set_uv_texel_density", icon="MOD_MESHDEFORM")
    col.operator("view3d.pixunwrap_rectify", icon="MOD_BEVEL")

    col = layout.column(align=True)
    op = col.operator("view3d.pixunwrap_uv_flip", text="Flip Horizontal")
    op.flip_axis = "X"
    op.modify_texture = modify_texture
    op = col.operator("view3d.pixunwrap_uv_flip", text="Flip Vertical")
    op.flip_axis = "Y"
    op.modify_texture = modify_texture

    row = layout.row(align=True)
    op = row.operator("view3d.pixunwrap_uv_rot_90", text="Rot 90° CCW")
    op.modify_texture = modify_texture
    op.clockwise = False
    op = row.operator("view3d.pixunwrap_uv_rot_90", text="Rot 90° CW")
    op.modify_texture = modify_texture
    op.clockwise = True

    fold_col = layout.column()
    fold_col.enabled = not modify_texture
    row = fold_col.row()
    row.prop(scene, "pixunwrap_fold_sections", text="Folds")
    row.prop(scene, "pixunwrap_fold_alternate", text="Mirror")
    row = fold_col.row(align=True)
    fold_x = row.operator("view3d.pixunwrap_uv_grid_fold", text="Fold X")
    fold_x.x_sections = scene.pixunwrap_fold_sections
    fold_x.y_sections = 1
    fold_x.alternate = scene.pixunwrap_fold_alternate
    fold_y = row.operator("view3d.pixunwrap_uv_grid_fold", text="Fold Y")
    fold_y.x_sections = 1
    fold_y.y_sections = scene.pixunwrap_fold_sections
    fold_y.alternate = scene.pixunwrap_fold_alternate

    col = layout.column(align=True)
    row = col.row(align=True)
    row.enabled = not modify_texture
    op = row.operator("view3d.pixunwrap_nudge_islands", icon="BACK", text="")
    op.move_x = -1
    op.move_y = 0
    op = row.operator("view3d.pixunwrap_nudge_islands", icon="SORT_DESC", text="")
    op.move_x = 0
    op.move_y = 1
    op = row.operator("view3d.pixunwrap_nudge_islands", icon="SORT_ASC", text="")
    op.move_x = 0
    op.move_y = -1
    op = row.operator("view3d.pixunwrap_nudge_islands", icon="FORWARD", text="")
    op.move_x = 1
    op.move_y = 0
    row.separator()
    row.label(text="Nudge")

    col = layout.column(align=True)
    col.enabled = not modify_texture
    col.operator("view3d.pixunwrap_stack_islands", icon="DUPLICATE")
    col.operator("view3d.pixunwrap_randomize_islands", icon="PIVOT_BOUNDBOX")

    col = layout.column(align=True)
    op = col.operator("view3d.pixunwrap_island_to_free_space", icon="UV_ISLANDSEL")
    op.modify_texture = modify_texture
    op = col.operator("view3d.pixunwrap_repack_uvs", icon="ALIGN_BOTTOM")
    op.modify_texture = modify_texture


def _draw_texture_bake(self, context):
    layout = self.layout
    obj = context.active_object
    buttonlabel = "Bake Texture"
    if obj and len(obj.data.uv_layers) >= 2:
        target_uv = obj.data.uv_layers.active
        source_uv = next((uv for uv in obj.data.uv_layers if uv != target_uv), None)
        texture_name = None
        if obj.active_material and obj.active_material.use_nodes:
            for node in obj.active_material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    texture_name = node.image.name
                    break
        if source_uv and texture_name:
            buttonlabel = f'Bake into "{texture_name}"'
            layout.label(text=f"'{source_uv.name}' -> '{target_uv.name}'")
    else:
        layout.label(text="Select an object that has 2 UV maps")

    layout.operator("view3d.pixunwrap_transfer_texture", text=buttonlabel)


def _draw_paint_tools(self, context):
    layout = self.layout
    col = layout.column(align=True)
    col.operator(PIXUNWRAP_OT_swap_eraser.bl_idname)
    col.operator("view3d.pixunwrap_setup_pixel_brush", icon="SNAP_ON")


# ---------------------------------------------------------------------------
# VIEW_3D panels
# ---------------------------------------------------------------------------

class PIXUNWRAP_PT_texture_setup(bpy.types.Panel):
    bl_label = "Texture Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    bl_options = {"DEFAULT_CLOSED"}
    draw = _draw_texture_setup


class PIXUNWRAP_PT_unwrapping(bpy.types.Panel):
    bl_label = "Unwrapping"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    draw = _draw_unwrapping


class PIXUNWRAP_PT_uv_editing(bpy.types.Panel):
    bl_label = "UV Editing"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    draw = _draw_uv_editing


class PIXUNWRAP_PT_texture_bake(bpy.types.Panel):
    bl_label = "Texture Bake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    bl_options = {"DEFAULT_CLOSED"}
    draw = _draw_texture_bake


class PIXUNWRAP_PT_paint_tools(bpy.types.Panel):
    bl_label = "Paint Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    draw = _draw_paint_tools


# ---------------------------------------------------------------------------
# IMAGE_EDITOR panels
# ---------------------------------------------------------------------------

class PIXUNWRAP_PT_texture_setup_ie(bpy.types.Panel):
    bl_label = "Texture Setup"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    bl_options = {"DEFAULT_CLOSED"}
    draw = _draw_texture_setup


class PIXUNWRAP_PT_unwrapping_ie(bpy.types.Panel):
    bl_label = "Unwrapping"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    draw = _draw_unwrapping


class PIXUNWRAP_PT_uv_editing_ie(bpy.types.Panel):
    bl_label = "UV Editing"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    draw = _draw_uv_editing


class PIXUNWRAP_PT_texture_bake_ie(bpy.types.Panel):
    bl_label = "Texture Bake"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    bl_options = {"DEFAULT_CLOSED"}
    draw = _draw_texture_bake


class PIXUNWRAP_PT_paint_tools_ie(bpy.types.Panel):
    bl_label = "Paint Tools"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Pixel Unwrapper"
    draw = _draw_paint_tools
