"""
ST7735 Display Configuration Loader
Loads and parses TOML configuration files for ST7735 displays
"""

import toml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class DisplayConfig:
    """Display configuration data structure"""
    name: str
    manufacturer: str
    model: str
    published_resolution: Tuple[int, int]  # (width, height)
    pins: Dict[str, int]  # pin assignments
    calibration: Dict[str, any]  # calibration data
    
    @property
    def width(self) -> int:
        """Get published display width"""
        return self.published_resolution[0]
    
    @property
    def height(self) -> int:
        """Get published display height"""
        return self.published_resolution[1]
    
    @property
    def usable_width(self) -> int:
        """Get calibrated usable width"""
        return self.calibration['right'] - self.calibration['left'] + 1
    
    @property
    def usable_height(self) -> int:
        """Get calibrated usable height"""
        return self.calibration['bottom'] - self.calibration['top'] + 1
    
    @property
    def orientation(self) -> str:
        """Get display orientation"""
        return self.calibration.get('orientation', 'landscape')
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get calibrated center point (x, y)"""
        center_list = self.calibration.get('center', [0, 0])
        return tuple(center_list)


def load_display_config(config_file: str) -> DisplayConfig:
    """
    Load and parse a display configuration file
    
    Args:
        config_file: Path to TOML config file (e.g., 'DueLCD01.config')
    
    Returns:
        DisplayConfig object with parsed configuration data
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        toml.TomlDecodeError: If config file is invalid TOML
        KeyError: If required fields are missing
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_path, 'r') as f:
        data = toml.load(f)
    
    # Validate required sections
    required_sections = ['device', 'pinout', 'calibration']
    for section in required_sections:
        if section not in data:
            raise KeyError(f"Missing required section [{section}] in config file")
    
    # Create DisplayConfig object
    return DisplayConfig(
        name=data['device']['name'],
        manufacturer=data['device'].get('manufacturer', 'Unknown'),
        model=data['device'].get('model', 'Unknown'),
        published_resolution=tuple(data['device']['published_resolution']),
        pins=data['pinout'],
        calibration=data['calibration']
    )


def find_config_files(search_dir: str = '.') -> Dict[str, Path]:
    """
    Find all display config files in a directory
    
    Args:
        search_dir: Directory to search (default: current directory)
    
    Returns:
        Dictionary mapping device names to config file paths
        Example: {'DueLCD01': Path('DueLCD01.config'), ...}
    """
    search_path = Path(search_dir)
    config_files = {}
    
    # Look for .config files
    for config_file in search_path.glob('*.config'):
        try:
            config = load_display_config(str(config_file))
            config_files[config.name] = config_file
        except (toml.TomlDecodeError, KeyError) as e:
            # Skip invalid config files
            print(f"Warning: Skipping invalid config file {config_file}: {e}")
            continue
    
    return config_files


def get_config_by_device_name(device_name: str, search_dir: str = '.') -> Optional[DisplayConfig]:
    """
    Load config for a specific device by name
    
    Args:
        device_name: Device name (e.g., 'DueLCD01')
        search_dir: Directory to search for config files
    
    Returns:
        DisplayConfig object if found, None otherwise
    """
    config_files = find_config_files(search_dir)
    
    if device_name in config_files:
        return load_display_config(str(config_files[device_name]))
    
    return None


def print_config_info(config: DisplayConfig):
    """Print human-readable configuration information"""
    print(f"\n=== Display Configuration: {config.name} ===")
    print(f"Manufacturer: {config.manufacturer}")
    print(f"Model: {config.model}")
    print(f"Published Resolution: {config.width}x{config.height}")
    print(f"\nPin Assignments:")
    for pin_name, pin_num in config.pins.items():
        print(f"  {pin_name.upper():3s} -> Pin {pin_num}")
    print(f"\nCalibration:")
    print(f"  Orientation: {config.orientation}")
    print(f"  Usable Area: {config.usable_width}x{config.usable_height}")
    print(f"  Bounds: left={config.calibration['left']}, right={config.calibration['right']}, "
          f"top={config.calibration['top']}, bottom={config.calibration['bottom']}")
    print(f"  Center: {config.center}")
    print()


if __name__ == '__main__':
    """Test the config loader"""
    import sys
    
    if len(sys.argv) > 1:
        # Load specific config file
        config_file = sys.argv[1]
        try:
            config = load_display_config(config_file)
            print_config_info(config)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    else:
        # Find and display all configs
        print("Searching for display config files...")
        configs = find_config_files()
        
        if not configs:
            print("No valid config files found.")
            sys.exit(1)
        
        print(f"Found {len(configs)} display configuration(s):")
        for device_name, config_path in configs.items():
            print(f"  - {device_name}: {config_path}")
        
        print("\nLoading all configurations...")
        for device_name in configs:
            config = get_config_by_device_name(device_name)
            if config:
                print_config_info(config)
