# Pronomar to a5

## Instalación
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Configuración
```bash
cp config/default_template.yml config/default.yml
# Ingresar los parámetros de configuración en config/default.yml
```
## Uso
Descarga archivo NetCDF de Pronomar
```bash
python get_prono.py
```
Convierte en formato a5 json
```bash
python read_prono.py -o data/corrida.json
```
Convierte en formato a5 json y guarda en base de datos
```bash
python read_prono.py -o data/corrida_guardada.json -u
```
Descarga, convierte en formato a5 json y guarda en base de datos
```bash
python run.py -o data/corrida_guardada.json -u
```