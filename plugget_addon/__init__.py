import logging

bl_info = {
    "name": "Plugget",
    "description": "easy install Plugget",
    "author": "Hannes D",
    "version": (1, 0),
    "blender": (2, 91, 0),
    "location": "Preferences/Add-ons",
    "category": "Development",
}

import sys, os
import bpy
import subprocess
import importlib
from pathlib import Path
import importlib.metadata
import requests
import shutil


plugget_package_name = "plugget"
output_log = "Installing..."
packages_found = []


def get_latest_version(package_name):
    """get the latest version number for a package on PyPi"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        version = data["info"]["version"]
        return version
    else:
        raise Exception(f"Failed to retrieve version for {package_name} from PyPI")


def plugget_is_installed():
    try:
        import plugget
        return True
    except ImportError:
        return False


def latest_plugget_is_installed():
    try:
        latest_available_version = get_latest_version(plugget_package_name)
        installed_version = importlib.metadata.version(plugget_package_name)
        if installed_version == latest_available_version:
            return True
        else:
            logging.warning(f"Plugget Installed version: {installed_version}, latest version: {latest_available_version}")
    except:
        return False


def install_plugget():
    global output_log

    if latest_plugget_is_installed():
        return

    blender_user_site_packages = Path(bpy.utils.script_path_user()) / "addons/modules"  # appdata

    # Get the path to the Python executable used by Blender
    python_executable = sys.executable

    # todo confirm folder deleted, also dist info folder
    # delete
    plugget_module = blender_user_site_packages / "plugget"
    # also check for dist info folder(s)
    # e.g. plugget-0.0.5.dist-info
    # iter all folders in blender_user_site_packages

    # delete old plugget module and metadata
    print("delete old plugget module and metadata")
    delete_dirs = [plugget_module]
    for p in plugget_module.iterdir():
        if p.name.startswith("plugget-") and p.is_dir() and p.name.endswith(".dist-info"):
            delete_dirs.append(p)
    for p in delete_dirs:
        if p.exists():
            try:
                print(f"Deleting {p}")
                shutil.rmtree(p)
            except Exception as e:
                logging.error(e)

    # Run the command to install the plugget package using pip and the Python executable
    try:
        command = [python_executable, '-m', 'pip', 'install', 'plugget', '-t', str(blender_user_site_packages), '--upgrade']
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

    def get_plugget_path(self, attr_name: str) -> str:
        """Get attr by name from plugget.settings as string, used to get path-constants"""
        try:
            import plugget
            return str(getattr(plugget.settings, attr_name))
        except ImportError:
            return ""

    def draw(self, context):
        global packages_found

        layout = self.layout

        if plugget_is_installed():
            row = layout.row()
            row.label(text="dev folders:")
            row.operator("util.open_folder", text="installed packages", icon="FILE_FOLDER").folder_path = self.get_plugget_path("INSTALLED_DIR")
            row.operator("util.open_folder", text="settings", icon="FILE_FOLDER").folder_path = self.get_plugget_path("PLUGGET_DIR")
            row.operator("util.open_folder", text="temp", icon="FILE_FOLDER").folder_path = self.get_plugget_path("TEMP_PLUGGET")

            row = layout.row()
            search_btn = row.operator("plugget.search_packages", text="Search")
            search_txt = row.prop(self, "text_input")
            # todo row.scale_x = 2

            for meta_packages in packages_found:
                row = layout.row()
                row.label(text=meta_packages.package_name)

                # meta_packages
                # row.label(text=package.version) # todo replace with dropdown

                if any(x.is_installed for x in meta_packages.packages):
                # if package.is_installed:
                    # update_btn = row.operator("plugget.update_package", text="Update")  # todo
                    uninstall_row = row.row()
                    uninstall_row.alert = True
                    uninstall_btn = uninstall_row.operator("plugget.uninstall_package", text="Uninstall")
                    uninstall_btn.package_name = meta_packages.package_name
                else:
                    install_btn = row.operator("plugget.install_package", text="Install")
                    install_btn.package_name = meta_packages.package_name
                    install_btn.tooltip = meta_packages.description if hasattr(meta_packages, "description") else meta_packages.package_name

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
            layout.operator("plugget.install_plugget", text="Install Plugget (requires internet connection)")

            for l in output_log.splitlines():
                if "ERROR" in l:
                    col = layout.column()
                    col.alert = True
                    col.label(text=l)
                else:
                    layout.label(text=l)


class InstallPluggetOperator(bpy.types.Operator):
    bl_idname = "plugget.install_plugget"
    bl_label = "Install the Plugget Python module"

    def execute(self, context):
        install_plugget()
        return {'FINISHED'}


class InstallPluggetPackageOperator(bpy.types.Operator):
    bl_idname = "plugget.install_package"
    bl_label = "Install a Plugget Package"
    package_name: bpy.props.StringProperty(
        name="package_name",
        description="package name",
        default=""
    )
    tooltip: bpy.props.StringProperty()

    def execute(self, context):
        import plugget.commands as cmd
        cmd.install(self.package_name) # todo output log
        return {'FINISHED'}

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip


class UninstallPluggetPackageOperator(bpy.types.Operator):
    bl_idname = "plugget.uninstall_package"
    bl_label = "Uninstall a Plugget Package"
    package_name: bpy.props.StringProperty(
        name="package_name",
        description="package name",
        default=""
    )

    def execute(self, context):
        import plugget.commands as cmd
        print(self.package_name)
        cmd.uninstall(self.package_name) # todo output log
        return {'FINISHED'}


class SearchPluggetPackageOperator(bpy.types.Operator):
    bl_idname = "plugget.search_packages"
    bl_label = "Search Plugget Packages"

    def execute(self, context):
        import plugget.commands as cmd
        global packages_found
        addon_prefs = context.preferences.addons[__name__].preferences
        result = cmd.search(addon_prefs.text_input)
        packages_found = result
        return {'FINISHED'}


class OpenFolderOperator(bpy.types.Operator):
    bl_idname = "util.open_folder"
    bl_label = "Open Folder"
    bl_icon = "FILE_FOLDER"

    folder_path: bpy.props.StringProperty()

    def execute(self, context):
        print("open self.folder_path", self.folder_path)
        if os.name == 'nt':
            os.startfile(self.folder_path)
        elif os.name == 'posix':
            if sys.platform == 'darwin':
                os.system(f'open "{self.folder_path}"')
            else:
                os.system(f'xdg-open "{self.folder_path}"')

        return {'FINISHED'}


def register():
    bpy.utils.register_class(PluggetPreferences)
    bpy.utils.register_class(SearchPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetPackageOperator)
    bpy.utils.register_class(UninstallPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetOperator)
    bpy.utils.register_class(OpenFolderOperator)
    install_plugget()


def unregister():
    bpy.utils.unregister_class(PluggetPreferences)
    bpy.utils.unregister_class(SearchPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetPackageOperator)
    bpy.utils.unregister_class(UninstallPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetOperator)
    bpy.utils.unregister_class(OpenFolderOperator)
























