class OverlayTemplates:

    overlayhtml = """
 <!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="overlaystyle.css">
<meta http-equiv="refresh" content="1">
</head>
<body>

<h1 class = "team1">
{0}<br>
</h1>

<h1 class = "team2">
{1}<br>
</h1>

<div style="clear: both;"></div>
</body>
</html> 
    """

    overlaycss = """

body {
  background-color: transparent;
}

h1 {
  color: navy;
  font-size:2vw; 
  }


.team1 {
	color: white;
	float: right;
	margin-right: 20px;

	}

.team2 {
	color: white;
	float: left;
	margin-left: 20px;
	
}


    """