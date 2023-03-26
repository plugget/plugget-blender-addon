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
import importlib
from pathlib import Path


output_log = "Installing..."
packages_found = []


def plugget_is_installed():
    try:
        import plugget
        return True
    except ImportError:
        return False

def install_plugget():
    global output_log

    if plugget_is_installed():
        return

    blender_user_site_packages = Path(bpy.utils.script_path_user()) / "addons/modules"  # appdata

    # Get the path to the Python executable used by Blender
    python_executable = sys.executable

    # Run the command to install the plugget package using pip and the Python executable
    try:
        command = [python_executable, '-m', 'pip', 'install', 'plugget', '-t', str(blender_user_site_packages)]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        print(output.decode())
        output_log = output.decode()
        importlib.invalidate_caches()  # refresh dynamic added py modules, ensuring they are importable
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        output_log = e.output.decode()


class PluggetPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    output = output_log
    text_input: bpy.props.StringProperty(
        name="",
        description="Search package name",
        default=""
    )

    def draw(self, context):
        global packages_found

        layout = self.layout

        if plugget_is_installed():

            import plugget.commands as cmds
            installed_packages = [x.package_name for x in cmds.list()]

            layout.label(text="Plugget is installed")

            row = layout.row()
            search_btn = row.operator("wm.search_plugget_packages", text="Search")
            search_txt = row.prop(self, "text_input")
            # todo row.scale_x = 2

            print(packages_found)
            for package in packages_found:
                row = layout.row()
                row.label(text=package.package_name)
                row.label(text=package.version)
                if package.package_name not in installed_packages:
                    install_btn = row.operator("wm.install_plugget_package", text="Install")
                    install_btn.package_name = package.package_name
                else:
                    row.label(text="Installed")
                # row.label(text=package.description)
                # row.operator("wm.install_package", text="Install")

            # todo show buttons to search packages.
            # +----------------------+----------+
            # |        Search        |  Update  |
            # +----------------------+----------+
            # | Package A v1.0       | Install  |
            # | Short description    |          |
            # +----------------------+----------+
            # | Package B v1.2       | Install  |
            # | Short description    |          |
            # +----------------------+----------+
            # | Package C v2.1       | Update   |
            # | Short description    |          |
            # +----------------------+----------+

        else:
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

class InstallPluggetPackageOperator(bpy.types.Operator):
    bl_idname = "wm.install_plugget_package"
    bl_label = "Install a Plugget Package"
    # package: bpy.props.PointerProperty(type=plugget.data.Package)
    package_name: bpy.props.StringProperty(
        name="package_name",
        description="package name",
        default=""
    )

    def execute(self, context):
        import plugget.commands as cmd
        cmd.install(self.package_name) # todo output log
        return {'FINISHED'}


class SearchPluggetPackageOperator(bpy.types.Operator):
    bl_idname = "wm.search_plugget_packages"
    bl_label = "Search Plugget Packages"

    def execute(self, context):
        import plugget.commands as cmd
        global packages_found
        addon_prefs = context.preferences.addons[__name__].preferences
        result = cmd.search(addon_prefs.text_input)
        print(result)
        packages_found = result
        # self.report({'INFO'}, "Updated packages_found value")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PluggetPreferences)
    bpy.utils.register_class(SearchPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetOperator)
    install_plugget()


def unregister():
    bpy.utils.unregister_class(PluggetPreferences)
    bpy.utils.unregister_class(SearchPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetOperator)
























