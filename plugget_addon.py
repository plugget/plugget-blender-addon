bl_info = {
    "name": "Plugget",
    "description": "easy install Plugget",
    "author": "Hannes D",
    "version": (1, 0),
    "blender": (2, 91, 0),
    "location": "Preferences/Add-ons",
    "category": "Development",
}

import sys
import bpy
import subprocess
from pathlib import Path


output_log = ""


def install_plugget():
    global output_log

    try:
        import plugget
        return
    except ImportError:
        pass

    blender_user_site_packages = Path(bpy.utils.script_path_user()) / "addons/modules"  # appdata

    # Get the path to the Python executable used by Blender
    python_executable = sys.executable

    # Run the command to install the plugget package using pip and the Python executable
    try:
        command = [python_executable, '-m', 'pip', 'install', 'plugget', '-t', str(blender_user_site_packages)]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        print(output.decode())
        output_log = output.decode()
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        output_log = e.output.decode()


class PluggetPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    output = output_log

    def draw(self, context):
        layout = self.layout

        try:
            import plugget
            layout.label(text="Plugget is installed")
        except ImportError:
            layout.operator("wm.install_plugget", text="Install Plugget (requires internet connection)")

            for l in output_log.splitlines():
                if "ERROR" in l:
                    col = layout.column()
                    col.alert = True
                    col.label(text=l)
                else:
                    layout.label(text=l)


class InstallPluggetOperator(bpy.types.Operator):
    bl_idname = "wm.install_plugget"
    bl_label = "Install the Plugget Python module"

    def execute(self, context):
        install_plugget()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PluggetPreferences)
    bpy.utils.register_class(InstallPluggetOperator)
    install_plugget()


def unregister():
    bpy.utils.unregister_class(PluggetPreferences)
    bpy.utils.unregister_class(InstallPluggetOperator)
























