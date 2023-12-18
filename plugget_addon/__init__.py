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


def _register_plugget_config():
    """register the addon's plugget-config with plugget"""
    import importlib.resources
    import plugget.settings
    with importlib.resources.path('plugget_addon.resources', 'config.json') as p:
        settings_path = Path(p)
        plugget.settings.registered_settings_paths.add(settings_path)


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
        import traceback
        traceback.print_exc()
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
    """
    PIP install plugget & it's dependencies if not already installed
    """
    global output_log

    if latest_plugget_is_installed():
        return

    blender_user_site_packages = Path(bpy.utils.script_path_user()) / "addons" / "modules"  # appdata
    blender_user_site_packages.mkdir(parents=True, exist_ok=True)

    # Get the path to the Python executable used by Blender
    python_executable = sys.executable

    # todo confirm folder deleted, also dist info folder
    # delete
    plugget_module = blender_user_site_packages / "plugget"
    # also check for dist info folder(s)
    # e.g. plugget-0.0.5.dist-info
    # iter all folders in blender_user_site_packages

    # delete old plugget module and metadata
    logging.debug("delete old plugget module and metadata")
    delete_dirs = [plugget_module]
    for p in blender_user_site_packages.iterdir():
        if p.name.startswith("plugget-") and p.is_dir() and p.name.endswith(".dist-info"):
            delete_dirs.append(p)
    for p in delete_dirs:
        if p.exists():
            try:
                logging.debug(f"Deleting {p}")
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
    
    advanced_mode: bpy.props.BoolProperty(
        name="Advanced Mode",
        description="Toggle advanced mode to show additional options",
        default=False
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

            # Add a checkbox to toggle advanced mode
            row.prop(self, "advanced_mode", text="Advanced")

            if self.advanced_mode:
                local_script_dir = bpy.utils.script_path_user()
                local_addons_dir = str(Path(local_script_dir) / "addons")
                # hide button sunder a dropwdown
                row.operator(OpenFolderOperator.bl_idname, text="blender addons", icon="BLENDER").folder_path = local_addons_dir
                row.operator(OpenFolderOperator.bl_idname, text="package configs", icon="FILE_FOLDER").folder_path = self.get_plugget_path("INSTALLED_DIR")
                row.operator(OpenFolderOperator.bl_idname, text="plugget settings", icon="FILE_FOLDER").folder_path = self.get_plugget_path("PLUGGET_DIR")
                row.operator(OpenFolderOperator.bl_idname, text="plugget temp", icon="FILE_FOLDER").folder_path = self.get_plugget_path("TEMP_PLUGGET")

            row = layout.row()
            list_btn = row.operator(ListPluggetPackageOperator.bl_idname, text="List installed", icon="COLLAPSEMENU")
            search_btn = row.operator(SearchPluggetPackageOperator.bl_idname, text="Search", icon="VIEWZOOM")
            search_txt = row.prop(self, "text_input")

            self._draw_package_list(layout) 

        else:
            # If plugget isn't installed, draw a button to install it
            layout.operator(InstallPluggetOperator.bl_idname, text="Install Plugget (requires internet connection)")

            for l in output_log.splitlines():
                if "ERROR" in l:
                    col = layout.column()
                    col.alert = True
                    col.label(text=l)
                else:
                    layout.label(text=l)

    def _draw_package_list(self, layout):
        """Draw UI for packages found"""
        
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

        global packages_found
        for meta_packages in packages_found:
            row = layout.row()
            row.label(text=meta_packages.package_name)

            # meta_packages
            # row.label(text=package.version) # todo replace with dropdown

            # Add a button to open a URL
            url_button = row.operator("wm.url_open", text="", icon="URL")
            url =  meta_packages.repo_url
            if url:
                url_button.url = url
            else:
                url_button.enabled = False
            
            if any(x.is_installed for x in meta_packages.packages):
            # if package.is_installed:
                # update_btn = row.operator("plugget.update_package", text="Update")  # todo
                uninstall_row = row.row()
                uninstall_row.alert = True  # color the button red
                button = uninstall_row.operator(UninstallPluggetPackageOperator.bl_idname, text="Uninstall")
            else:
                button = row.operator(InstallPluggetPackageOperator.bl_idname, text="Install")
            button.package_name = meta_packages.package_name
            button.tooltip = meta_packages.description if hasattr(meta_packages, "description") else meta_packages.package_name


class InstallPluggetOperator(bpy.types.Operator):
    """Install the Plugget Python module"""    
    bl_idname = "plugget.install_plugget"
    bl_label = "Install the Plugget Python module"

    def execute(self, context):
        install_plugget()
        return {'FINISHED'}


class InstallPluggetPackageOperator(bpy.types.Operator):
    """Install a Plugget Package"""
    bl_idname = "plugget.install_package"
    bl_label = "Install a Plugget Package"
    package_name: bpy.props.StringProperty(
        name="package_name",
        description="package name",
        default=""
    )
    tooltip: bpy.props.StringProperty()  # dynamic tooltip
    # meta_package: "plugget.MetaPackage"

    @classmethod
    def description(cls, context, properties):
        """return the tooltip for the operator, which overrides self.__class__.__doc__"""
        return f"Install {properties.tooltip}"

    def execute(self, context):
        import plugget.commands as cmd
        cmd.install(self.package_name) # todo output log
        return {'FINISHED'}


class UninstallPluggetPackageOperator(bpy.types.Operator):
    """Uninstall a Plugget Package"""
    bl_idname = "plugget.uninstall_package"
    bl_label = "Uninstall a Plugget Package"
    package_name: bpy.props.StringProperty(
        name="package_name",
        description="package name",
        default=""
    )
    tooltip: bpy.props.StringProperty()  # dynamic tooltip
    
    @classmethod
    def description(cls, context, properties):
        """return the tooltip for the operator, which overrides self.__class__.__doc__"""
        return f"Uninstall {properties.tooltip}"

    def execute(self, context):
        import plugget.commands as cmd
        print(self.package_name)
        cmd.uninstall(self.package_name) # todo output log
        return {'FINISHED'}


class SearchPluggetPackageOperator(bpy.types.Operator):
    """Search Plugget Packages"""
    bl_idname = "plugget.search_packages"
    bl_label = "Search Plugget Packages"

    def execute(self, context):
        import plugget.commands as cmd
        global packages_found
        addon_prefs = context.preferences.addons[__name__].preferences
        result = cmd.search(addon_prefs.text_input)
        packages_found = result
        return {'FINISHED'}
    

class ListPluggetPackageOperator(bpy.types.Operator):
    """List installed Plugget Packages"""
    bl_idname = "plugget.list_packages"
    bl_label = "list Plugget Packages"

    def execute(self, context):
        import plugget.commands as cmd
        global packages_found
        addon_prefs = context.preferences.addons[__name__].preferences
        result = cmd.list()
        packages_found = result
        return {'FINISHED'}


class OpenFolderOperator(bpy.types.Operator):
    """Open a folder in file explorer"""
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
    bpy.utils.register_class(ListPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetPackageOperator)
    bpy.utils.register_class(UninstallPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetOperator)
    bpy.utils.register_class(OpenFolderOperator)
    install_plugget()
    _register_plugget_config()


def unregister():
    bpy.utils.unregister_class(PluggetPreferences)
    bpy.utils.unregister_class(SearchPluggetPackageOperator)
    bpy.utils.unregister_class(ListPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetPackageOperator)
    bpy.utils.unregister_class(UninstallPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetOperator)
    bpy.utils.unregister_class(OpenFolderOperator)
