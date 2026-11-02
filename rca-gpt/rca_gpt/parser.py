"""
Log parser module - extracts structured data from raw logs
"""
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
import yaml


class LogParser:
    """Parses raw application logs into structured CSV format"""
    
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Regex pattern for log format: [LEVEL] TIMESTAMP - MESSAGE
        self.pattern = re.compile(
            r"\[(?P<level>\w+)\]\s+"
            r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+"
            r"(?P<message>.*)"
        )
    
    def parse_log_file(self, log_file_path=None):
        """
        Parse log file and return DataFrame
        
        Args:
            log_file_path: Path to log file (uses config if None)
            
        Returns:
            DataFrame with columns: level, timestamp, message
        """
        if log_file_path is None:
            log_file_path = self.config['logging']['app_log_file']
        
        log_path = Path(log_file_path)
        
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        entries = []
        
        with open(log_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                match = self.pattern.match(line.strip())
                if match:
                    entries.append(match.groupdict())
                else:
                    print(f"Warning: Could not parse line {line_num}: {line.strip()}")
        
        return pd.DataFrame(entries)
    
    def save_to_csv(self, df, output_path=None, mode='append'):
        """
        Save parsed logs to CSV
        
        Args:
            df: DataFrame to save
            output_path: Where to save (uses config if None)
            mode: 'append' or 'overwrite'
        """
        if output_path is None:
            output_path = self.config['data']['raw_logs_csv']
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists
        file_exists = output_path.exists()
        
        if mode == 'append' and file_exists:
            # Append without header
            df.to_csv(output_path, mode='a', header=False, index=False)
            print(f"Appended {len(df)} entries to {output_path}")
        else:
            # Write with header (overwrite or new file)
            df.to_csv(output_path, index=False)
            print(f"Wrote {len(df)} entries to {output_path}")
        
        return output_path
    
    def parse_and_save(self, log_file_path=None, output_path=None, mode='append'):
        """
        Convenience method: parse log file and save to CSV
        """
        df = self.parse_log_file(log_file_path)
        return self.save_to_csv(df, output_path, mode)


if __name__ == "__main__":
    # Example usage
    parser = LogParser()
    parser.parse_and_save()