"""Read CCNB/CAVD NET point and periodic connection records."""
from pathlib import Path


def read_channel_net(path: Path):
    """Read NET rows, retaining periodic images and reverse connections."""
    path = Path(path)
    sites, connections = [], []
    channel_id, dimension, section = None, None, None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if not fields:
                continue
            if fields[0] in {"channeId", "channelId"}:
                channel_id, dimension, section = int(fields[1]), None, None
            elif fields[0] == "dimensionality":
                dimension = int(fields[1])
            elif "Interstitial table:" in line:
                section = "sites"
            elif "Connection table:" in line:
                section = "connections"
            elif section == "sites":
                if len(fields) != 6:
                    raise ValueError(f"Unexpected site row in {path}: {line.strip()}")
                sites.append(dict(channel_id=channel_id, dimension=dimension,
                                  node_id=int(fields[0]), label=int(fields[1]),
                                  frac_coords=list(map(float, fields[2:5])),
                                  radius_A=float(fields[5])))
            elif section == "connections":
                if len(fields) != 10:
                    raise ValueError(f"Unexpected connection row in {path}: {line.strip()}")
                connections.append(dict(channel_id=channel_id, dimension=dimension,
                                        start=int(fields[0]), end=int(fields[1]),
                                        image=list(map(int, fields[2:5])),
                                        bottleneck_frac_coords=list(map(float, fields[5:8])),
                                        bottleneck_radius_A=float(fields[8]),
                                        length_A=float(fields[9])))
    return sites, connections
