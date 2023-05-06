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
import bpy
import requests
import json


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



class GitHubFavoritesPanel(bpy.types.AddonPreferences):
    bl_idname = "GitHubFavoritesPanel" #__name__

    github_username: bpy.props.StringProperty(
        name="GitHub Username",
        description="Enter your GitHub username",
        default=""
    )

    github_token: bpy.props.StringProperty(
        name="GitHub Personal Access Token",
        description="Enter your GitHub Personal Access Token",
        default=""
    )

    def draw(self, context):
        layout = self.layout

        # Create a box to group the UI elements
        box = layout.box()

        # Add a label to the box
        box.label(text="GitHub Favorites")

        # Add a text field for entering the username
        box.prop(self, "github_username")

        # Add a text field for entering the Personal Access Token
        box.prop(self, "github_token")

        # Add a button to retrieve the user's favorites
        box.operator("object.get_github_favorites")

class GetGitHubFavoritesOperator(bpy.types.Operator):
    bl_idname = "object.get_github_favorites"
    bl_label = "Get Favorites"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        username = prefs.github_username
        # token = prefs.github_token

        # headers = {
        #     "Authorization": f"token {token}"
        # }
        url = f"https://api.github.com/users/{username}/starred"

        try:
            response = requests.get(url) #, headers=headers)
            if response.ok:
                favorites = json.loads(response.text)
                print(favorites)
                for favorite in favorites:
                    print(favorite["full_name"])
            else:
                print(f"Error: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

        return {"FINISHED"}


class PluggetPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    output = output_log
    text_input: bpy.props.StringProperty(
        name="",
        description="Search package name",
        default=""
    )

    github_username: bpy.props.StringProperty(
        name="GitHub Username",
        description="Enter your GitHub username",
        default=""
    )

    github_token: bpy.props.StringProperty(
        name="GitHub Personal Access Token",
        description="Enter your GitHub Personal Access Token",
        default=""
    )


    def draw(self, context):
        global packages_found

        layout = self.layout

        if plugget_is_installed():
            row = layout.row()
            search_btn = row.operator("wm.search_plugget_packages", text="Search")
            search_txt = row.prop(self, "text_input")
            # todo row.scale_x = 2

            for package in packages_found:
                row = layout.row()

                # starred / favorited
                if package.is_starred():
                    star_btn = row.label(icon="FUND")
                else:
                    star_btn = row.label(icon="HEART")
                    # star_btn.package_name = package.package_name


                # stars
                stars = package.get_stars()
                # if more than 1000 stars, show 1k
                if stars >= 1000:
                    stars = f"{stars/1000:.1f}k"
                row.label(text=str(f"{stars} ★"))

                # name
                row.label(text=package.package_name)

                # version
                row.label(text=package.version)

                # button
                if package.is_installed:
                    # update_btn = row.operator("wm.update_plugget_package", text="Update")  # todo
                    uninstall_row = row.row()
                    uninstall_row.alert = True
                    uninstall_btn = uninstall_row.operator("wm.uninstall_plugget_package", text="Uninstall")
                    uninstall_btn.package_name = package.package_name
                else:
                    install_btn = row.operator("wm.install_plugget_package", text="Install")
                    install_btn.package_name = package.package_name
                    install_btn.tooltip = package.description if hasattr(package, "description") else package.package_name



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


        # Create a box to group the UI elements
        box = layout.box()

        # Add a label to the box
        box.label(text="GitHub Favorites")

        # Add a text field for entering the username
        box.prop(self, "github_username")

        # Add a text field for entering the Personal Access Token
        box.prop(self, "github_token")

        # Add a button to retrieve the user's favorites
        box.operator("object.get_github_favorites")


class InstallPluggetOperator(bpy.types.Operator):
    bl_idname = "wm.install_plugget"
    bl_label = "Install the Plugget Python module"

    def execute(self, context):
        install_plugget()
        return {'FINISHED'}

class InstallPluggetPackageOperator(bpy.types.Operator):
    bl_idname = "wm.install_plugget_package"
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
    bl_idname = "wm.uninstall_plugget_package"
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
    bl_idname = "wm.search_plugget_packages"
    bl_label = "Search Plugget Packages"

    def execute(self, context):
        import plugget.commands as cmd
        global packages_found
        addon_prefs = context.preferences.addons[__name__].preferences
        result = cmd.search(addon_prefs.text_input)
        packages_found = result
        return {'FINISHED'}


def register():
    bpy.utils.register_class(GitHubFavoritesPanel)
    bpy.utils.register_class(GetGitHubFavoritesOperator)

    bpy.utils.register_class(PluggetPreferences)
    bpy.utils.register_class(SearchPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetPackageOperator)
    bpy.utils.register_class(UninstallPluggetPackageOperator)
    bpy.utils.register_class(InstallPluggetOperator)
    install_plugget()


def unregister():
    bpy.utils.unregister_class(GitHubFavoritesPanel)
    bpy.utils.unregister_class(GetGitHubFavoritesOperator)

    bpy.utils.unregister_class(PluggetPreferences)
    bpy.utils.unregister_class(SearchPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetPackageOperator)
    bpy.utils.unregister_class(UninstallPluggetPackageOperator)
    bpy.utils.unregister_class(InstallPluggetOperator)
























