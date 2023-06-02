# MetaConnect


## 1) Direct ssh connections to specific servers based on their metadata
The connect.py establishes ssh connections.

### Servers
To select specific server use the `-s` or `--server` options:
```
./metaconnect -s onyx
./metaconnect --server onyx
```
The text is parsed using fuzzy search so every command below means the same thing. 
```
./metaconnect -s ski
./metaconnect -s sirit
./metaconnect -s skirit
```

### Storages
You can select a storage insted of specific server using  `-d`, `--dist` or `--storage` options:
```
./metaconnect -d praha1
./metaconnect --disk praha1
./metaconnect --sotorage praha1
```
### Organizations
To select specific organization the `-o` or `--org` or `--organization` is used:
```
./metaconnect -o elixir
./metaconnect --org cerit
./metaconnect --organizaton meta
```

### Help and index selection
The `-h` or `--help` prints list of numbers that can be used instead of typing specific strings.

```
./metaconnect --organization 0
```

### Useful commands
It is quite convinient to use symbolic link.
```
ln -s "$(realpaht metaconnect.py)"  ~/.local/bin/metaconnect
```



## 2) Filling of the ~/.ssh/config file
The fill_config.py creates multiple shortcuts in the ~/.ssh/config.
This enables to use 
```
ssh skirit
```
istead of 
```
ssh user@skirit.metacentrum.cz -i ~/.ssh/key
```

## 3) Setting up the Kerberos authentication
The `setup_kerberos.sh` configuration installs requirements and adds configurations to the `~/.ssh/config`.
The ticket can be obtained for up to 7 days using the `initkrb.sh` (you must change username).

