# PBS-Pro-Toolkit
Contains scripts that makes massively parallel and cross-platform processing bareble on MetaCentrum infrastructure (PBS-Pro).

---
## metaconnect
Contains scripts that:
- set up Kerberos auth.
- creates `metaconnect` that runs servers based on specific requirements.
  - `metaconnect --org cerit` connects to brno3-cerit
  - `metaconnect --storage praha1` connects to tarkil
- scripts that fills `~/.ssh/config` with shortcuts. So `ssh tarkil` runs `ssh username@tarkil.metacentrum.cz` ...


---
## cloudDB
Series of scipts and pyhton modules that setups MongoDB database on the MetacentrumCloud.
You can fill the database with work and safely mark them as completed.


---
## create_singularity
Create singularity (and docker) container.

<!--
Contains Makefile that builds singularity ubuntu-based container with python-3.11.
It also installs python packages found in requirements.txt. 

MetaCentrum:
The script must be run on builder.metacentrum.cz because of privilages. 

## parallel_run
TODO
-->
