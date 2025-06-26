import yaml

with open("configs/tournaments_2023_atp_ausopen.yaml") as f:
    yml = yaml.safe_load(f)
    print("Loaded YAML keys:", yml.keys())
    tournaments = yml.get("tournaments", [])
    if tournaments:
        print("First tournament dict keys:", tournaments[0].keys())
        print("First tournament entry:", tournaments[0])
        print("tournament:", tournaments[0].get("tournament"))
        print("year:", tournaments[0].get("year"))
        print("label:", tournaments[0].get("label"))
    else:
        print("No tournaments found in YAML!")
