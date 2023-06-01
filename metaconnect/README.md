# MetaConnect

## 1) Filling of the ~/.ssh/config file
The fill_config.py creates multiple shortcuts in the ~/.ssh/config.
This enables to use 
```
ssh skirit
```
istead of 
```
ssh user@skirit.metacentrum.cz -i ~/.ssh/key
```

## 2) Direct ssh connections to specific servers based on their metadata
The connect.py establishes ssh connections.

### Servers
To select specific server use the `-s` or `--server` options:
```
./connect -s onyx
./connect --server onyx
```
The text is parsed using fuzzy search so every command below means the same thing. 
```
./connect -s ski
./connect -s sirit
./connect -s skirit
```

### Storages
You can select a storage insted of specific server using  `-d`, `--dist` or `--storage` options:
```
./connect -d praha1
./connect --disk praha1
./connect --sotorage praha1
```
### Organizations
To select specific organization the `-o` or `--org` or `--organization` is used:
```
./connect -o elixir
./connect --org cerit
./connect --organizaton meta
```

### Help and index selection
The `-h` or `--help` prints list of numbers that can be used instead of typing specific strings.

```
./connect --organization 0
```
