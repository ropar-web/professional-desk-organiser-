STREAMLIT CLOUD FIX

1. Put requirements.txt and packages.txt in the SAME GitHub folder as app.py.
2. Replace the old requirements.txt.
3. Commit the changes.
4. Streamlit should redeploy automatically. If not, open Manage app and reboot.

This fix pins CadQuery/OCP and installs the Linux GL/X11 libraries used by OCP.
