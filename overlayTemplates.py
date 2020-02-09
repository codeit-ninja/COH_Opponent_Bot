class OverlayTemplates:

    overlayhtml = """
 <!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="overlaystyle.css">
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
	background-color: transparent;
  }
    
#container{width:100%;
	font-size: 30px; 

}


#countryflagimg{
	display: inline;
}

#factionflagimg{
	display: inline;
}

#textVariables {
	display: inline;
}




#rankimg {
		position: relative;
		top: 10px;
		display: inline;
}

#opponentTeam {

	  position : absolute;
	  top: -10px; /* This will move it px up */
	  color: white;
	  float: left;
	  margin-left: 60%;
	  background-color: rgba(0, 0, 0, 0.8);
	  }
  
#playerTeam {

	  position: relative;
	  top: -10px; /* This will move it px up */
	  color: white;
	  float: right;
	  margin-right: 60%;


	  background-color: rgba(0, 0, 0, 0.8);
  }
  
  

    



    """