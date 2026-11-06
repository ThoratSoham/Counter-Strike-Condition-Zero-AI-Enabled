//
// AI TEAMMATES CHAT OVERLAY SCHEME (Low-Opacity Black Background)
//
Scheme
{
	//////////////////////// COLORS ///////////////////////////
	Colors
	{
		// Low-opacity black background (~45% opacity: 115 / 255) behind bot chat text
		"WindowBG"				"0 0 0 115"
		"ControlBG"				"0 0 0 0"
		"BorderBright"			"0 0 0 70"
		"BorderDark"			"0 0 0 70"
		"BaseText"				"245 245 245 255"
		"ControlText"			"245 245 245 255"

		// High-contrast team & sound colors on top of the low-opacity black backdrop
		"TutorTextClassDefault"	"245 245 245 255"	// Default crisp off-white
		"TutorTextClass2"		"255 135 130 255"	// Terrorist Warm Red
		"TutorTextClass4"		"155 215 255 255"	// Counter-Terrorist Ice Blue
		"TutorTextClass8"		"145 245 160 255"	// Sound / System Mint Green
		"TutorTextClass256"		"255 225 100 255"	// Match Notice Gold
	}

	///////////////////// BASE SETTINGS ////////////////////////
	BaseSettings
	{
		"FgColor"			"TutorTextClassDefault"
		"BgColor"			"ControlBG"
		"LabelBgColor"		"ControlBG"
		"SubPanelBgColor"	"ControlBG"
		"WindowFgColor"		"TutorTextClassDefault"
		"WindowBgColor"		"WindowBG"
		"ChatBgColor"		"WindowBG"
	}

	//////////////////////// FONTS /////////////////////////////
	Fonts
	{
		"Default"
		{
			"1"
			{
				"name"			"Verdana"
				"tall"			"13"
				"weight"		"600"
				"yres"			"480 599"
				"dropshadow"	"1"
			}
			"2"
			{
				"name"			"Verdana"
				"tall"			"14"
				"weight"		"600"
				"yres"			"600 767"
				"dropshadow"	"1"
			}
			"3"
			{
				"name"			"Verdana"
				"tall"			"15"
				"weight"		"600"
				"yres"			"768 1023"
				"antialias"		"1"
				"dropshadow"	"1"
			}
			"4"
			{
				"name"			"Verdana"
				"tall"			"18"
				"weight"		"600"
				"yres"			"1024 6000"
				"antialias"		"1"
				"dropshadow"	"1"
			}
		}
	}

	//////////////////// BORDERS //////////////////////////////
	Borders
	{
		BaseBorder
		{
			"inset" "0 0 1 1"
			Left
			{
				"1"
				{
					"color" "BorderDark"
					"offset" "0 1"
				}
			}
			Right
			{
				"1"
				{
					"color" "BorderBright"
					"offset" "1 0"
				}
			}
			Top
			{
				"1"
				{
					"color" "BorderDark"
					"offset" "0 0"
				}
			}
			Bottom
			{
				"1"
				{
					"color" "BorderBright"
					"offset" "0 0"
				}
			}
		}
	}
}
