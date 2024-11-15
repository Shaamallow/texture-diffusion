import bpy


class HistoryItem(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty(name="History ID")
    prompt: bpy.props.StringProperty(name="Prompt")
    seed: bpy.props.IntProperty(name="Seed")
    cfg_scale: bpy.props.FloatProperty(name="CFG")
    n_steps: bpy.props.IntProperty(name="Steps")
    scheduler: bpy.props.StringProperty(name="Scheduler")
    negative_prompt: bpy.props.StringProperty(name="Negative Prompt")
    uuid: bpy.props.StringProperty(name="UUID")
    url: bpy.props.StringProperty(name="Prompt")
    fetching_attempts: bpy.props.IntProperty(name="Seed")
    mesh: bpy.props.StringProperty(name="Mesh")
    received: bpy.props.BoolProperty(name="Received", default=False)


class HistoryProperties(bpy.types.PropertyGroup):

    history_collection: bpy.props.CollectionProperty(type=HistoryItem)

    # Counter for generation ID
    history_counter: bpy.props.IntProperty(name="History Counter", default=0)


def register():
    bpy.utils.register_class(HistoryItem)
    bpy.utils.register_class(HistoryProperties)
    bpy.types.Scene.history_properties = bpy.props.PointerProperty(
        type=HistoryProperties
    )


def unregister():
    bpy.utils.unregister_class(HistoryItem)
    bpy.utils.unregister_class(HistoryProperties)
    del bpy.types.Scene.history_properties
