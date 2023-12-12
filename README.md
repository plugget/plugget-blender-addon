⚠️ For a more advanced UI, see the [plugget qt addon](https://github.com/plugget/plugget-qt-addon) repo  

# Plugget installer add-on
A Blender add-on to install [plugget](https://github.com/hannesdelbeke/plugget) packages.<br>
It uses native Blender UI with minimal dependencies to provide a simple but stable addon to get started with plugget.<br>

<img src="https://user-images.githubusercontent.com/3758308/228056063-2c98f14b-1aea-4150-90b1-d8a0599e6b08.png" width="600"></img>

## Installation
Before install, ensure you have:
- [Git for Windows](https://git-scm.com/download/win) installed
- Windows OS

<details>
<summary>Using the blend file installer (recommended)</summary>

- Download and open the [blend file](https://github.com/hannesdelbeke/plugget-blender-addon/raw/main/installer/install_plugget_addon.blend), and run the scripts inside to auto install the add-on.
- Or run [this](https://github.com/plugget/plugget-blender-addon/blob/main/installer/auto_install_addon.py) code in Blender
  
</details>


<details>
<summary>Manual installation</summary>

1. download this repo as a zip and extract the zip. ensure you have the file `plugget_addon.py`
2. Go to `Edit/Preferences... (menu) -> add-ons (tab)` and click `Install` button
3. Browse to the `plugget_addon.py`
4. In the search bar, type `plugget` and enable the add-on
5. On enable, the plugget-installer add-on will automatically install plugget. And show any errors below the install button.
You should now see a message saying `plugget installed successfully`.
If something failed you can always try again by clicking the install button, or disable and re-enable the add-on

![installation instructions screenshot](install_addon.jpg)
  
</details>

### community
- blenderartists [thread](https://blenderartists.org/t/plugget-a-search-engine-installer-for-add-ons/1456558)


If this tool is helpfull, you can ⭐ star it on the github page,
just click the ⭐ star button in the top-right of this page.
