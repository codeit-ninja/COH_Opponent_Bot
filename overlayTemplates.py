class OverlayTemplates:

	overlayhtml = """
 <!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="overlaystyle.css">
<meta http-equiv="content-type" content="text-html; charset=utf-8">
<meta http-equiv="refresh" content="2">
</head>
<body>
<div id="container">
<div id = "playerTeam">
{0}
</div>
<div id = "opponentTeam">
{1}
</div>
</div>
<div style="clear: both;"></div>
</body>
</html> 
"""

	overlaycss = """



body {
	position: relative;
	background-color: transparent;
	padding: 0px;
	
  }
  
html {
	position: relative;
	padding: 0px;
}
  
	
#container{width:100%;
	position: relative;
	top: -7px;
	font-size: 20px; 
}


#countryflagimg{
	position: relative;
	display: inline;
	top: 3px;
}

#countryflagimg img{
	height:20px;
}

#factionflagimg{
	position: relative;
	display: inline;
	top: 3px;
}

#factionflagimg img{
	height:20px;
}

#rankimg {
	position: relative;
	top: 5px;
	display: inline;
}

#rankimg img {
	height:30px ;
}

#textVariables {
	position: relative;
	display: inline;
	top: 0px;
}

#nonVariableText{
	position: relative;
	display: inline;
	top: 0px;
}

#opponentTeam {

	  position : absolute;
	  top: 0px; 
	  color: white;
	  float: left;
	  margin-left: 58%;
	  background-color: rgba(0, 0, 0, 0.8);
	  text-align: left;
	  }
  
#playerTeam {

	  position: relative;
	  top: 0px; 
	  color: white;
	  float: right;
	  margin-right: 58%;
	  background-color: rgba(0, 0, 0, 0.8);
	  text-align: right;
  }
	



	"""