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
{0}
</h1>

<h1 class = "team2">
{1}
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
  font-size: 30px; 
  }


.team1 {
	position : relative;
	top: -20px; /* This will move it 20px up */
	color: white;
	float: left;
	margin-right: 5px;
	margin-left: 300px;
	background-color: rgba(0, 0, 0, 0.8);
	}

.team2 {
	position: relative;
	top: -20px; /* This will move it 20px up */
	color: white;
	float: right;
	margin-left: 5px;
	margin-right: 300px;
	background-color: rgba(0, 0, 0, 0.8);
}




    """