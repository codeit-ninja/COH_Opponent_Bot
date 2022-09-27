class OverlayTemplates:
    """Templates for HTML and CSS output files."""

    overlayhtml = """
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="{}">
<meta http-equiv="content-type" content="text-html; charset=utf-8">
    <script>
        var previousDate;
        var backgroundScript = setInterval(checkIfFileHasChanged, 5000);

        function checkIfFileHasChanged() {
            date = new Date(window.location.pathname.lastModified);
            if (previousDate != null) {
                if (date.getTime() !== previousDate.getTime()) {
                    window.location.reload();
                }
            }
            previousDate = date;
        }

        const chunk = (chunks) => {
            let chunk = [];
            let chunked = [];
            
            chunks.forEach(child => {
                if(child.tagName.toLowerCase() !== 'br') {
                    chunk.push(child);

                    return;
                }

                chunked.push(chunk);
                chunk = [];
            });

            return chunked;
        }

        const createPlayerElement = (player, index) => {
            const playerDiv = document.createElement('div')

            playerDiv.classList.add(`player`);
            playerDiv.classList.add(`player-${index + 1}`);

            player.forEach(el => playerDiv.appendChild(el));

            return playerDiv;
        }

        document.addEventListener('DOMContentLoaded', () => {
            const playerTeam = document.querySelector('.playerTeam');
            const opponentTeam = document.querySelector('.opponentTeam');
            const childs = [...playerTeam.children];

            const playerTeamPlayers = chunk([...playerTeam.children]);
            const opponentTeamPlayers = chunk([...opponentTeam.children]);

            playerTeam.innerHTML = '';
            opponentTeam.innerHTML = '';

            playerTeamPlayers.forEach((player, index) => {
                const playerDiv = createPlayerElement(player, index);

                playerTeam.appendChild(playerDiv);
            });

            opponentTeamPlayers.forEach((player, index) => {
                const playerDiv = createPlayerElement(player, index);

                opponentTeam.appendChild(playerDiv);
            });
        })
    </script>
</head>
<body>
<div class="container">
<div class = "playerTeam">
{}
</div>
<div class = "opponentTeam">
{}
</div>
</div>
<div style="clear: both;"></div>
</body>
</html>
"""

    overlaycss = """

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Mono:wght@200;400&family=Special+Elite&display=swap');

body {
    position: relative;
    background-color: transparent;
    padding: 0pt;
}

html {
    position: relative;
    padding: 0pt;
}

body, html {
    padding: 0;
    margin: 0;
}

.container {
    display: flex;
    max-width: 690px;
    margin: 0 auto;
    justify-content: space-between;
    height: 100vh;
    position: relative;
    top: 0pt;
    font-size: 14px;
}

/* Try some bs here */
.playerTeam,
.opponentTeam {
    display: flex;
    flex-direction: column;
}

.nonVariableText, 
.countryflagimg {
    display: none;
}

.player {
    font-family: 'Special Elite', cursive;
    display: flex;
    align-items: center;
    color: white;
    text-shadow: 2px 2px black;
}

.player .name {
    position: relative;
    top: -1px;
}

.rankimg img,
.factionflagimg img  {
    max-width: 31px;
}

.factionflagimg img {
    position: relative;
    top: 2px;
}

.rankimg {
    margin-left: auto;
}

.player-3 {
    margin-top: auto;
}

    """
