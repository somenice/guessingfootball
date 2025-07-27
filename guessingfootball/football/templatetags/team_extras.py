from django import template

register = template.Library()

@register.simple_tag
def team_logo(team_abbr, size='normal'):
    """Generate a CSS-based team logo placeholder"""
    size_class = {
        'small': 'small',
        'normal': '',
        'large': 'large'
    }.get(size, '')
    
    return f'<span class="team-logo {team_abbr} {size_class}">{team_abbr}</span>'

@register.filter
def team_colors(team_abbr):
    """Get team colors for styling"""
    # Team color mappings
    colors = {
        # AFC East
        'BUF': {'primary': '#00338D', 'secondary': '#C60C30'},
        'MIA': {'primary': '#008E97', 'secondary': '#FC4C02'},
        'NE': {'primary': '#002244', 'secondary': '#C60C30'},
        'NYJ': {'primary': '#125740', 'secondary': '#000000'},
        
        # AFC North
        'BAL': {'primary': '#241773', 'secondary': '#000000'},
        'CIN': {'primary': '#FB4F14', 'secondary': '#000000'},
        'CLE': {'primary': '#311D00', 'secondary': '#FF3C00'},
        'PIT': {'primary': '#FFB612', 'secondary': '#000000'},
        
        # AFC South
        'HOU': {'primary': '#03202F', 'secondary': '#A71930'},
        'IND': {'primary': '#002C5F', 'secondary': '#A2AAAD'},
        'JAX': {'primary': '#006778', 'secondary': '#D7A22A'},
        'TEN': {'primary': '#0C2340', 'secondary': '#4B92DB'},
        
        # AFC West
        'DEN': {'primary': '#FB4F14', 'secondary': '#002244'},
        'KC': {'primary': '#E31837', 'secondary': '#FFB81C'},
        'LV': {'primary': '#000000', 'secondary': '#A5ACAF'},
        'LAC': {'primary': '#0080C6', 'secondary': '#FFC20E'},
        
        # NFC East
        'DAL': {'primary': '#003594', 'secondary': '#041E42'},
        'NYG': {'primary': '#0B2265', 'secondary': '#A71930'},
        'PHI': {'primary': '#004C54', 'secondary': '#A5ACAF'},
        'WAS': {'primary': '#5A1414', 'secondary': '#FFB612'},
        
        # NFC North
        'CHI': {'primary': '#0B162A', 'secondary': '#C83803'},
        'DET': {'primary': '#0076B6', 'secondary': '#B0B7BC'},
        'GB': {'primary': '#203731', 'secondary': '#FFB612'},
        'MIN': {'primary': '#4F2683', 'secondary': '#FFC62F'},
        
        # NFC South
        'ATL': {'primary': '#A71930', 'secondary': '#000000'},
        'CAR': {'primary': '#0085CA', 'secondary': '#BFC0BF'},
        'NO': {'primary': '#D3BC8D', 'secondary': '#000000'},
        'TB': {'primary': '#D50A0A', 'secondary': '#FF7900'},
        
        # NFC West
        'ARI': {'primary': '#97233F', 'secondary': '#000000'},
        'SF': {'primary': '#AA0000', 'secondary': '#B3995D'},
        'SEA': {'primary': '#002244', 'secondary': '#69BE28'},
        'LA': {'primary': '#003594', 'secondary': '#FFA300'},
    }
    
    return colors.get(team_abbr, {'primary': '#666666', 'secondary': '#333333'})

@register.simple_tag
def team_logo_with_name(team, size='normal'):
    """Generate team logo with full name"""
    logo = team_logo(team.name, size)
    return f'{logo} <span class="team-name">{team.full_name or team.name}</span>'