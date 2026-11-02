"""
RCA-GPT Command Line Interface
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Use relative imports since we're inside the package now
from .parser import LogParser
from .trainer import IncidentClassifier
from .predictor import IncidentPredictor
from .monitor import LogMonitor
from .db.manager import IncidentDatabase



def cmd_monitor(args):
    """Start monitoring (now with database integration)"""
    monitor = LogMonitor(args.config)
    
    if args.once:
        # Single check
        count = monitor.monitor_once()
        print(f"\n✅ Check complete: {count} incidents detected")
    else:
        # Continuous
        monitor.monitor_continuous(interval=args.interval)


def cmd_history(args):
    """Show incident history"""
    db = IncidentDatabase(args.config)
    
    # Get incidents
    if args.days:
        cutoff = datetime.utcnow() - timedelta(days=args.days)
        incidents = db.get_incidents_in_timerange(cutoff, incident_type=args.type)
    else:
        incidents = db.get_recent_incidents(limit=args.limit, incident_type=args.type)
    
    if not incidents:
        print("No incidents found")
        return
    
    print(f"\n📊 Found {len(incidents)} incident(s)\n")
    print(f"{'ID':<6} {'Type':<20} {'Severity':<8} {'Count':<6} {'Last Seen':<20}")
    print("=" * 80)
    
    for inc in incidents:
        last_seen = inc.last_seen.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{inc.id:<6} {inc.incident_type:<20} {inc.severity:<8} {inc.occurrence_count:<6} {last_seen}")


def cmd_show(args):
    """Show detailed incident information"""
    db = IncidentDatabase(args.config)
    
    # Get incident
    incident = db.get_incident_by_id(args.incident_id)
    
    if not incident:
        print(f"❌ Incident #{args.incident_id} not found")
        return
    
    # Display incident details
    print(f"\n🔍 Incident #{incident.id}")
    print("=" * 80)
    print(f"Type: {incident.incident_type}")
    print(f"Severity: {incident.severity}")
    print(f"Message: {incident.message_template}")
    print(f"Fingerprint: {incident.fingerprint}")
    print(f"First seen: {incident.first_seen.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Last seen: {incident.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total occurrences: {incident.occurrence_count}")
    
    # Get recent occurrences
    print(f"\n📋 Recent Occurrences (last {args.limit}):")
    print("=" * 80)
    
    occurrences = db.get_incident_occurrences(incident.id, limit=args.limit)
    
    for i, occ in enumerate(occurrences, 1):
        timestamp = occ.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        status = "✅ Resolved" if occ.resolved else "⏳ Unresolved"
        print(f"\n{i}. [{timestamp}] {status}")
        print(f"   Message: {occ.full_message}")
        
        if args.verbose:
            # Show context
            ctx_before = occ.get_context_before()
            ctx_after = occ.get_context_after()
            
            if ctx_before:
                print("   Context before:")
                for log in ctx_before[-3:]:
                    print(f"     [{log.get('level', 'N/A')}] {log.get('message', 'N/A')}")
            
            if ctx_after:
                print("   Context after:")
                for log in ctx_after[:3]:
                    print(f"     [{log.get('level', 'N/A')}] {log.get('message', 'N/A')}")
        
        if occ.resolved and occ.resolution_notes:
            print(f"   Resolution: {occ.resolution_notes}")
            print(f"   Resolved by: {occ.resolved_by} at {occ.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}")


def cmd_stats(args):
    """Show incident statistics"""
    db = IncidentDatabase(args.config)
    
    # Overall summary
    summary = db.get_database_summary()
    
    print("\n📊 DATABASE SUMMARY")
    print("=" * 80)
    print(f"Total unique incidents: {summary['total_unique_incidents']}")
    print(f"Total occurrences: {summary['total_occurrences']}")
    print(f"Resolved: {summary['resolved_occurrences']}")
    print(f"Unresolved: {summary['unresolved_occurrences']}")
     
    if summary['oldest_incident']:
        print(f"Oldest incident: {summary['oldest_incident']}")
    if summary['newest_incident']:
        print(f"Newest incident: {summary['newest_incident']}")
    
    # Stats by type
    print(f"\n📈 INCIDENT STATISTICS (Last {args.days} days)")
    print("=" * 80)
    
    stats = db.get_incident_stats(days=args.days)
    
    if not stats:
        print("No incidents in the specified time period")
        return
    
    print(f"{'Type':<20} {'Unique':<10} {'Total':<10} {'Avg/Incident':<15}")
    print("-" * 80)
    
    for incident_type, data in sorted(stats.items(), key=lambda x: x[1]['total_occurrences'], reverse=True):
        print(f"{incident_type:<20} {data['unique_incidents']:<10} {data['total_occurrences']:<10} {data['avg_occurrences_per_incident']:<15.1f}")
    
    # Top incidents
    print(f"\n🔥 TOP {args.top} INCIDENTS (Last {args.days} days)")
    print("=" * 80)
    
    top_incidents = db.get_top_incidents(limit=args.top, days=args.days)
    
    for i, inc in enumerate(top_incidents, 1):
        print(f"{i}. [{inc.incident_type}] {inc.message_template[:60]}")
        print(f"   Occurrences: {inc.occurrence_count} | Last seen: {inc.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def cmd_resolve(args):
    """Mark an incident occurrence as resolved"""
    db = IncidentDatabase(args.config)
    
    occurrence = db.mark_resolved(
        occurrence_id=args.occurrence_id,
        resolution_notes=args.notes,
        resolved_by=args.by if args.by else "cli-user"
    )
    
    if occurrence:
        print(f"✅ Occurrence #{occurrence.id} marked as resolved")
        print(f"   Incident: #{occurrence.incident_id}")
        print(f"   Resolution: {occurrence.resolution_notes}")
    else:
        print(f"❌ Occurrence #{args.occurrence_id} not found")


def cmd_search(args):
    """Search incidents by message content"""
    db = IncidentDatabase(args.config)
    
    incidents = db.search_incidents(args.query)
    
    if not incidents:
        print(f"No incidents found matching: {args.query}")
        return
    
    print(f"\n🔍 Found {len(incidents)} incident(s) matching '{args.query}'\n")
    print(f"{'ID':<6} {'Type':<20} {'Message':<50}")
    print("=" * 80)
    
    for inc in incidents:
        msg = inc.message_template[:47] + "..." if len(inc.message_template) > 50 else inc.message_template
        print(f"{inc.id:<6} {inc.incident_type:<20} {msg}")


def cmd_export(args):
    """Export incidents to JSON"""
    db = IncidentDatabase(args.config)
    
    # Get incidents
    if args.days:
        cutoff = datetime.utcnow() - timedelta(days=args.days)
        incidents = db.get_incidents_in_timerange(cutoff)
    else:
        incidents = db.get_recent_incidents(limit=args.limit)
    
    # Convert to dict
    data = {
        'exported_at': datetime.utcnow().isoformat(),
        'incident_count': len(incidents),
        'incidents': []
    }
    
    for inc in incidents:
        incident_dict = inc.to_dict()
        
        # Include occurrences if requested
        if args.include_occurrences:
            occurrences = db.get_incident_occurrences(inc.id, limit=100)
            incident_dict['occurrences'] = [occ.to_dict() for occ in occurrences]
        
        data['incidents'].append(incident_dict)
    
    # Write to file
    output_file = args.output if args.output else f"incidents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Exported {len(incidents)} incidents to: {output_file}")

def cmd_similar(args):
    """Find similar incidents"""
    from .similarity import SimilarityMatcher
    
    matcher = SimilarityMatcher(args.config)
    results = matcher.get_similar_with_context(args.message, top_k=args.top)
    
    if not results:
        print("No similar incidents found")
        return
    
    print(f"\n🔍 Found {len(results)} similar incident(s):\n")
    
    for i, r in enumerate(results, 1):
        inc = r['incident']
        print(f"{i}. Incident #{inc['id']} ({r['similarity']:.0%} similar)")
        print(f"   Type: {inc['incident_type']}")
        print(f"   Message: {inc['message_template']}")
        print(f"   Occurrences: {inc['occurrence_count']}")
        
        if r['resolution']:
            print(f"   ✅ Resolution: {r['resolution']['notes']}")
        else:
            print(f"   ⏳ Unresolved")
        print()

def cmd_patterns(args):
    """Show discovered patterns"""
    from .patterns import PatternMiner
    
    miner = PatternMiner(args.config)
    patterns = miner.mine_patterns(days=args.days, min_support=args.min_support)
    
    if not patterns:
        print("No patterns found")
        return
    
    print(f"\n🔍 Found {len(patterns)} recurring pattern(s):\n")
    
    for i, p in enumerate(patterns, 1):
        print(f"{i}. {p['pattern']}")
        print(f"   Occurrences: {p['occurrences']}")
        print(f"   Avg cascade time: {p['avg_cascade_time_seconds']:.0f}s")
        print()

def cmd_timeline(args):
    """Show incident timeline"""
    from .timeline import TimelineAnalyzer
    
    analyzer = TimelineAnalyzer(args.config)
    timeline = analyzer.get_timeline(args.incident_id, 
                                     minutes_before=args.before,
                                     minutes_after=args.after)
    
    if not timeline:
        print(f"Incident #{args.incident_id} not found")
        return
    
    print(f"\n🕐 Timeline for Incident #{args.incident_id}")
    print("=" * 80)
    
    target_time = timeline['target_time']
    
    if timeline['original_sin']:
        os = timeline['original_sin']
        print(f"\n🔍 ORIGINAL SIN (First error before incident):")
        print(f"   {os['minutes_from_target']:.1f} min before: [{os['severity']}] {os['message']}")
    
    print(f"\n📋 Events ({len(timeline['events'])} total):\n")
    
    for event in timeline['events']:
        marker = "🎯" if event['is_target'] else "  "
        time_str = f"{event['minutes_from_target']:+.1f}min"
        severity_color = event['severity']
        
        print(f"{marker} {time_str:>8} [{severity_color:5}] {event['message'][:60]}")

def cmd_parse(args):
    """Parse logs to CSV using LogParser (best-effort wrapper)."""
    out = args.output if hasattr(args, 'output') and args.output else None
    try:
        # Try to construct LogParser with input if provided, else default
        parser = LogParser(args.input) if hasattr(args, 'input') and args.input else LogParser()
    except Exception:
        parser = LogParser()

    try:
        # Try common export method names — robust fallback
        if out and hasattr(parser, 'to_csv'):
            parser.to_csv(out, append=getattr(args, 'append', False))
            print(f"✅ Parsed logs written to {out}")
        elif out and hasattr(parser, 'parse_to_csv'):
            parser.parse_to_csv(out, append=getattr(args, 'append', False))
            print(f"✅ Parsed logs written to {out}")
        elif hasattr(parser, 'parse'):
            records = parser.parse()
            # If parse() returns list of dicts, write CSV; else dump lines
            if records and isinstance(records, list) and isinstance(records[0], dict):
                import csv
                out_file = out or 'parsed.csv'
                mode = 'a' if getattr(args, 'append', False) else 'w'
                with open(out_file, mode, newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    if mode == 'w':
                        writer.writeheader()
                    writer.writerows(records)
                print(f"✅ Parsed logs written to {out_file}")
            else:
                out_file = out or 'parsed.txt'
                mode = 'a' if getattr(args, 'append', False) else 'w'
                with open(out_file, mode) as f:
                    for r in records:
                        f.write(str(r) + "\n")
                print(f"✅ Parsed logs written to {out_file}")
        else:
            print("⚠️  LogParser does not expose a known export method (to_csv/parse_to_csv/parse).")
    except Exception as e:
        print("❌ Error while parsing logs:", e)
        raise


def cmd_train(args):
    """Train ML model / classifier (wrapper)."""
    try:
        trainer = IncidentClassifier(args.config)
    except Exception:
        trainer = IncidentClassifier()

    try:
        # Common API: trainer.train() or trainer.fit()
        if hasattr(trainer, 'train'):
            trainer.train()
        elif hasattr(trainer, 'fit'):
            trainer.fit()
        else:
            print("⚠️  IncidentClassifier has no train/fit method.")
            return
        print("✅ Training complete")
    except Exception as e:
        print("❌ Training failed:", e)
        raise


def cmd_predict(args):
    """Predict incident type for a single message or a batch file."""
    try:
        predictor = IncidentPredictor(args.config)
    except Exception:
        predictor = IncidentPredictor()

    try:
        if getattr(args, 'batch', None):
            # batch file: one message per line
            with open(args.batch, 'r') as f:
                msgs = [ln.strip() for ln in f if ln.strip()]
            for m in msgs:
                if hasattr(predictor, 'predict'):
                    res = predictor.predict(m)
                elif hasattr(predictor, 'infer'):
                    res = predictor.infer(m)
                else:
                    res = None
                print(m)
                print(" ->", res)
        else:
            message = getattr(args, 'message', None)
            if not message:
                print("❗ No message provided to predict")
                return
            if hasattr(predictor, 'predict'):
                res = predictor.predict(message)
            elif hasattr(predictor, 'infer'):
                res = predictor.infer(message)
            else:
                res = None
            print("Prediction:")
            print(res)
    except Exception as e:
        print("❌ Prediction failed:", e)
        raise


def main():
    parser = argparse.ArgumentParser(
        description='RCA-GPT: AI-powered Root Cause Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rca-gpt parse                        # Parse logs to CSV
  rca-gpt train                        # Train ML model
  rca-gpt predict "Invalid token"      # Classify single message
  rca-gpt monitor                      # Start monitoring with DB storage
  rca-gpt history --days 7             # Show incidents from last 7 days
  rca-gpt show 42                      # Show details for incident #42
  rca-gpt stats                        # Show database statistics
  rca-gpt search "timeout"             # Search for incidents
  rca-gpt resolve 15 "Restarted service"  # Mark occurrence as resolved
        """
    )
    
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to config file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='RCA-GPT v1.1.0 (Sprint 1 - Incident Database)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Parse command (unchanged)
    parse_parser = subparsers.add_parser('parse', help='Parse logs to CSV')
    parse_parser.add_argument('-i', '--input', help='Input log file')
    parse_parser.add_argument('-o', '--output', help='Output CSV file')
    parse_parser.add_argument('--append', action='store_true', help='Append to existing CSV')
    
    # Train command (unchanged)
    train_parser = subparsers.add_parser('train', help='Train ML model')
    
    # Predict command (unchanged)
    predict_parser = subparsers.add_parser('predict', help='Predict incident type')
    predict_group = predict_parser.add_mutually_exclusive_group(required=True)
    predict_group.add_argument('message', nargs='?', help='Log message to classify')
    predict_group.add_argument('-b', '--batch', help='File with messages (one per line)')
    
    # Monitor command (ENHANCED)
    monitor_parser = subparsers.add_parser('monitor', help='Start monitoring with DB storage')
    monitor_parser.add_argument('--interval', type=int, help='Check interval in seconds')
    monitor_parser.add_argument('--once', action='store_true', help='Run once then exit')
    
    # History command (NEW)
    history_parser = subparsers.add_parser('history', help='Show incident history')
    history_parser.add_argument('--days', type=int, help='Show incidents from last N days')
    history_parser.add_argument('--limit', type=int, default=50, help='Max incidents to show (default: 50)')
    history_parser.add_argument('--type', help='Filter by incident type')
    
    # Show command (NEW)
    show_parser = subparsers.add_parser('show', help='Show detailed incident info')
    show_parser.add_argument('incident_id', type=int, help='Incident ID to display')
    show_parser.add_argument('--limit', type=int, default=10, help='Max occurrences to show (default: 10)')
    show_parser.add_argument('-v', '--verbose', action='store_true', help='Show context logs')
    
    # Stats command (NEW)
    stats_parser = subparsers.add_parser('stats', help='Show incident statistics')
    stats_parser.add_argument('--days', type=int, default=7, help='Time period in days (default: 7)')
    stats_parser.add_argument('--top', type=int, default=10, help='Number of top incidents (default: 10)')
    
    # Resolve command (NEW)
    resolve_parser = subparsers.add_parser('resolve', help='Mark incident occurrence as resolved')
    resolve_parser.add_argument('occurrence_id', type=int, help='Occurrence ID')
    resolve_parser.add_argument('notes', help='Resolution notes')
    resolve_parser.add_argument('--by', help='Resolved by (default: cli-user)')
    
    # Search command (NEW)
    search_parser = subparsers.add_parser('search', help='Search incidents')
    search_parser.add_argument('query', help='Search term')
    
    # Export command (NEW)
    export_parser = subparsers.add_parser('export', help='Export incidents to JSON')
    export_parser.add_argument('-o', '--output', help='Output file (default: incidents_export_TIMESTAMP.json)')
    export_parser.add_argument('--days', type=int, help='Export incidents from last N days')
    export_parser.add_argument('--limit', type=int, default=1000, help='Max incidents to export')
    export_parser.add_argument('--include-occurrences', action='store_true', help='Include all occurrences')
    
    similar_parser = subparsers.add_parser('similar', help='Find similar incidents')
    similar_parser.add_argument('message', help='Message to compare')
    similar_parser.add_argument('--top', type=int, default=5, help='Number of results')

    patterns_parser = subparsers.add_parser('patterns', help='Show incident patterns')
    patterns_parser.add_argument('--days', type=int, default=30, help='Look back period')
    patterns_parser.add_argument('--min-support', type=int, default=3, help='Min occurrences')  

    timeline_parser = subparsers.add_parser('timeline', help='Show incident timeline')
    timeline_parser.add_argument('incident_id', type=int, help='Incident ID')
    timeline_parser.add_argument('--before', type=int, default=10, help='Minutes before')
    timeline_parser.add_argument('--after', type=int, default=5, help='Minutes after')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate function
    commands = {
    'parse': cmd_parse,
    'train': cmd_train,
    'predict': cmd_predict,
    'monitor': cmd_monitor,
    'history': cmd_history,
    'show': cmd_show,
    'stats': cmd_stats,
    'resolve': cmd_resolve,
    'search': cmd_search,
    'export': cmd_export,
    'similar': cmd_similar,     
    'patterns': cmd_patterns,    
    'timeline': cmd_timeline    
    }
    
    try:
        commands[args.command](args)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.config != 'config/config.yaml':
            print(f"   (Using config: {args.config})", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()