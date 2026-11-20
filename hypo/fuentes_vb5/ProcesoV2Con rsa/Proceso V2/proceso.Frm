VERSION 5.00
Object = "{9E66AE63-2E29-11CF-B978-0020AFE6BEB3}#1.0#0"; "CWANALY.OCX"
Object = "{D940E4E4-6079-11CE-88CB-0020AF6845F6}#1.0#0"; "CWUI.OCX"
Object = "{F9043C88-F6F2-101A-A3C9-08002B2F49FB}#1.2#0"; "COMDLG32.OCX"
Begin VB.Form Form1 
   AutoRedraw      =   -1  'True
   BackColor       =   &H00808080&
   Caption         =   "Proceso,de sismos del sistema de registro continuo, versión 2"
   ClientHeight    =   8310
   ClientLeft      =   1485
   ClientTop       =   1755
   ClientWidth     =   11805
   ForeColor       =   &H00808080&
   Icon            =   "proceso.frx":0000
   LinkTopic       =   "Form1"
   PaletteMode     =   1  'UseZOrder
   ScaleHeight     =   8310
   ScaleWidth      =   11805
   WindowState     =   2  'Maximized
   Begin VB.CommandButton Command14 
      Caption         =   "C"
      Height          =   255
      Left            =   9180
      TabIndex        =   68
      Top             =   3720
      Width           =   195
   End
   Begin VB.CommandButton Command13 
      Caption         =   "S"
      Height          =   255
      Left            =   9000
      TabIndex        =   67
      Top             =   3720
      Width           =   195
   End
   Begin CWUIControlsLib.CWGraph CWGraph3 
      Height          =   1035
      Index           =   0
      Left            =   1200
      TabIndex        =   63
      Top             =   600
      Width           =   8895
      _Version        =   65536
      _ExtentX        =   15690
      _ExtentY        =   1826
      _StockProps     =   68
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Small Fonts"
         Size            =   6
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Reset_0         =   0   'False
      CompatibleVers_0=   65536
      Graph_0         =   1
      ClassName_1     =   "CCWGraphFrame"
      opts_1          =   30
      C[0]_1          =   12632256
      Event_1         =   2
      ClassName_2     =   "CCWGFPlotEvent"
      Owner_2         =   1
      Plots_1         =   3
      ClassName_3     =   "CCWDataPlots"
      Array_3         =   1
      Editor_3        =   4
      ClassName_4     =   "CCWGFPlotArrayEditor"
      Owner_4         =   1
      Array[0]_3      =   5
      ClassName_5     =   "CCWDataPlot"
      opts_5          =   4194335
      Name_5          =   "Plot-1"
      C[0]_5          =   8388608
      C[1]_5          =   255
      C[2]_5          =   16711680
      C[3]_5          =   16776960
      Event_5         =   2
      X_5             =   6
      ClassName_6     =   "CCWAxis"
      opts_6          =   1567
      Name_6          =   "XAxis"
      Orientation_6   =   512
      format_6        =   7
      ClassName_7     =   "CCWFormat"
      Scale_6         =   8
      ClassName_8     =   "CCWScale"
      opts_8          =   90112
      rMin_8          =   23
      rMax_8          =   588
      dMax_8          =   10
      discInterval_8  =   1
      Radial_6        =   0
      Enum_6          =   9
      ClassName_9     =   "CCWEnum"
      Editor_9        =   10
      ClassName_10    =   "CCWEnumArrayEditor"
      Owner_10        =   6
      tickopts_6      =   2707
      major_6         =   1
      minor_6         =   0.5
      Y_5             =   11
      ClassName_11    =   "CCWAxis"
      opts_11         =   1567
      Name_11         =   "YAxis-1"
      Orientation_11  =   2067
      format_11       =   12
      ClassName_12    =   "CCWFormat"
      Scale_11        =   13
      ClassName_13    =   "CCWScale"
      opts_13         =   122880
      rMin_13         =   9
      rMax_13         =   59
      dMax_13         =   10
      discInterval_13 =   1
      Radial_11       =   0
      Enum_11         =   14
      ClassName_14    =   "CCWEnum"
      Editor_14       =   15
      ClassName_15    =   "CCWEnumArrayEditor"
      Owner_15        =   11
      tickopts_11     =   2711
      major_11        =   5
      minor_11        =   2.5
      LineStyle_5     =   1
      LineWidth_5     =   1
      BasePlot_5      =   0
      Axes_1          =   16
      ClassName_16    =   "CCWAxes"
      Array_16        =   2
      Editor_16       =   17
      ClassName_17    =   "CCWGFAxisArrayEditor"
      Owner_17        =   1
      Array[0]_16     =   6
      Array[1]_16     =   11
      DefaultPlot_1   =   18
      ClassName_18    =   "CCWDataPlot"
      opts_18         =   4194335
      Name_18         =   "[Template]"
      C[0]_18         =   65280
      C[1]_18         =   255
      C[2]_18         =   16711680
      C[3]_18         =   16776960
      Event_18        =   2
      X_18            =   6
      Y_18            =   11
      LineStyle_18    =   1
      LineWidth_18    =   1
      BasePlot_18     =   0
      Cursors_1       =   19
      ClassName_19    =   "CCWCursors"
      Array_19        =   3
      Editor_19       =   20
      ClassName_20    =   "CCWGFCursorArrayEditor"
      Owner_20        =   1
      Array[0]_19     =   21
      ClassName_21    =   "CCWCursor"
      opts_21         =   31
      Name_21         =   "Cursor-1"
      C[0]_21         =   255
      Event_21        =   2
      X_21            =   6
      Y_21            =   11
      XPos_21         =   1.05263161659241
      YPos_21         =   8.07106399536133
      SnapMode_21     =   1
      PointIndex_21   =   2
      ChrosshairStyle_21=   2
      PointStyle_21   =   3
      LockPlot_21     =   5
      Array[1]_19     =   22
      ClassName_22    =   "CCWCursor"
      opts_22         =   31
      Name_22         =   "Cursor-2"
      C[0]_22         =   65535
      Event_22        =   2
      X_22            =   6
      Y_22            =   11
      XPos_22         =   2.10526323318481
      YPos_22         =   9.84700107574463
      SnapMode_22     =   1
      PointIndex_22   =   4
      ChrosshairStyle_22=   2
      PointStyle_22   =   3
      LockPlot_22     =   5
      Array[2]_19     =   23
      ClassName_23    =   "CCWCursor"
      opts_23         =   31
      Name_23         =   "Cursor-3"
      C[0]_23         =   65280
      Event_23        =   2
      X_23            =   6
      Y_23            =   11
      XPos_23         =   3.15789484977722
      YPos_23         =   9.57886695861816
      SnapMode_23     =   1
      PointIndex_23   =   6
      ChrosshairStyle_23=   2
      PointStyle_23   =   12
      LockPlot_23     =   5
      TrackMode_1     =   2
      GraphBackground_1=   0
      GraphFrame_1    =   24
      ClassName_24    =   "CCWDrawObj"
      opts_24         =   28
      Image_24        =   25
      ClassName_25    =   "CCWPictImage"
      Bltin_25        =   -1  'True
      Stretch_25      =   -1  'True
      F_25            =   -2147483633
      B_25            =   -2147483633
      PlotFrame_1     =   26
      ClassName_26    =   "CCWDrawObj"
      opts_26         =   30
      C[1]_26         =   12632256
      Image_26        =   27
      ClassName_27    =   "CCWPictImage"
      Bltin_27        =   -1  'True
      Stretch_27      =   -1  'True
      Pict_27         =   1
      F_27            =   -2147483633
      B_27            =   12632256
   End
   Begin VB.CommandButton Command12 
      Caption         =   "P"
      Height          =   255
      Left            =   8820
      TabIndex        =   66
      Top             =   3720
      Width           =   195
   End
   Begin VB.Frame Frame1 
      Height          =   6675
      Left            =   10140
      TabIndex        =   45
      Top             =   900
      Width           =   735
      Begin VB.CheckBox Check2 
         Caption         =   "T"
         BeginProperty Font 
            Name            =   "Small Fonts"
            Size            =   6
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   195
         Left            =   180
         TabIndex        =   69
         Top             =   540
         Width           =   435
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "0"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   0
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   61
         Top             =   900
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "1"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   1
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   60
         Top             =   1260
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "2"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   2
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   59
         Top             =   1620
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "3"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   3
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   58
         Top             =   1980
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "4"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   4
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   57
         Top             =   2340
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "5"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   5
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   56
         Top             =   2700
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "6"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   6
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   55
         Top             =   3060
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "7"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   7
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   54
         Top             =   3420
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "8"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   8
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   53
         Top             =   3780
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "9"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   9
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   52
         Top             =   4140
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "10"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   10
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   51
         Top             =   4500
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "11"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   11
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   50
         Top             =   4860
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "12"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   12
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   49
         Top             =   5220
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "13"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   13
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   48
         Top             =   5580
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "14"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   14
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   47
         Top             =   5940
         Width           =   555
      End
      Begin VB.CheckBox Check1 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00C0C0C0&
         Caption         =   "15"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00800000&
         Height          =   255
         Index           =   15
         Left            =   60
         MaskColor       =   &H00808080&
         TabIndex        =   46
         Top             =   6300
         Width           =   555
      End
      Begin VB.Image Image1 
         Height          =   240
         Left            =   180
         Picture         =   "proceso.frx":0442
         Stretch         =   -1  'True
         Top             =   180
         Width           =   360
      End
   End
   Begin CWUIControlsLib.CWGraph CWGraph3 
      Height          =   1155
      Index           =   2
      Left            =   1200
      TabIndex        =   65
      Top             =   2520
      Width           =   8895
      _Version        =   65536
      _ExtentX        =   15690
      _ExtentY        =   2037
      _StockProps     =   68
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Small Fonts"
         Size            =   6
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Reset_0         =   0   'False
      CompatibleVers_0=   65536
      Graph_0         =   1
      ClassName_1     =   "CCWGraphFrame"
      opts_1          =   30
      C[0]_1          =   12632256
      Event_1         =   2
      ClassName_2     =   "CCWGFPlotEvent"
      Owner_2         =   1
      Plots_1         =   3
      ClassName_3     =   "CCWDataPlots"
      Array_3         =   1
      Editor_3        =   4
      ClassName_4     =   "CCWGFPlotArrayEditor"
      Owner_4         =   1
      Array[0]_3      =   5
      ClassName_5     =   "CCWDataPlot"
      opts_5          =   4194335
      Name_5          =   "Plot-1"
      C[0]_5          =   8388608
      C[1]_5          =   255
      C[2]_5          =   16711680
      C[3]_5          =   16776960
      Event_5         =   2
      X_5             =   6
      ClassName_6     =   "CCWAxis"
      opts_6          =   1567
      Name_6          =   "XAxis"
      Orientation_6   =   641
      LabelWidth_6    =   3
      format_6        =   7
      ClassName_7     =   "CCWFormat"
      Format_7        =   "*.015625"
      Scale_6         =   8
      ClassName_8     =   "CCWScale"
      opts_8          =   90112
      rMin_8          =   23
      rMax_8          =   581
      dMax_8          =   10
      discInterval_8  =   1
      Radial_6        =   0
      Enum_6          =   9
      ClassName_9     =   "CCWEnum"
      Editor_9        =   10
      ClassName_10    =   "CCWEnumArrayEditor"
      Owner_10        =   6
      tickopts_6      =   2707
      major_6         =   1
      minor_6         =   0.5
      Y_5             =   11
      ClassName_11    =   "CCWAxis"
      opts_11         =   1567
      Name_11         =   "YAxis-1"
      Orientation_11  =   2067
      format_11       =   12
      ClassName_12    =   "CCWFormat"
      Scale_11        =   13
      ClassName_13    =   "CCWScale"
      opts_13         =   122880
      rMin_13         =   9
      rMax_13         =   59
      dMax_13         =   10
      discInterval_13 =   1
      Radial_11       =   0
      Enum_11         =   14
      ClassName_14    =   "CCWEnum"
      Editor_14       =   15
      ClassName_15    =   "CCWEnumArrayEditor"
      Owner_15        =   11
      tickopts_11     =   2711
      major_11        =   5
      minor_11        =   2.5
      LineStyle_5     =   1
      LineWidth_5     =   1
      BasePlot_5      =   0
      Axes_1          =   16
      ClassName_16    =   "CCWAxes"
      Array_16        =   2
      Editor_16       =   17
      ClassName_17    =   "CCWGFAxisArrayEditor"
      Owner_17        =   1
      Array[0]_16     =   6
      Array[1]_16     =   11
      DefaultPlot_1   =   18
      ClassName_18    =   "CCWDataPlot"
      opts_18         =   4194335
      Name_18         =   "[Template]"
      C[0]_18         =   65280
      C[1]_18         =   255
      C[2]_18         =   16711680
      C[3]_18         =   16776960
      Event_18        =   2
      X_18            =   6
      Y_18            =   11
      LineStyle_18    =   1
      LineWidth_18    =   1
      BasePlot_18     =   0
      Cursors_1       =   19
      ClassName_19    =   "CCWCursors"
      Array_19        =   2
      Editor_19       =   20
      ClassName_20    =   "CCWGFCursorArrayEditor"
      Owner_20        =   1
      Array[0]_19     =   21
      ClassName_21    =   "CCWCursor"
      opts_21         =   31
      Name_21         =   "Cursor-1"
      C[0]_21         =   255
      Event_21        =   2
      X_21            =   6
      Y_21            =   11
      XPos_21         =   1.05263161659241
      YPos_21         =   8.07106399536133
      SnapMode_21     =   1
      PointIndex_21   =   2
      ChrosshairStyle_21=   2
      PointStyle_21   =   3
      LockPlot_21     =   5
      Array[1]_19     =   22
      ClassName_22    =   "CCWCursor"
      opts_22         =   31
      Name_22         =   "Cursor-2"
      C[0]_22         =   65535
      Event_22        =   2
      X_22            =   6
      Y_22            =   11
      XPos_22         =   2.10526323318481
      YPos_22         =   9.84700107574463
      SnapMode_22     =   1
      PointIndex_22   =   4
      ChrosshairStyle_22=   2
      PointStyle_22   =   3
      LockPlot_22     =   5
      TrackMode_1     =   2
      GraphBackground_1=   0
      GraphFrame_1    =   23
      ClassName_23    =   "CCWDrawObj"
      opts_23         =   28
      Image_23        =   24
      ClassName_24    =   "CCWPictImage"
      Bltin_24        =   -1  'True
      Stretch_24      =   -1  'True
      F_24            =   -2147483633
      B_24            =   -2147483633
      PlotFrame_1     =   25
      ClassName_25    =   "CCWDrawObj"
      opts_25         =   30
      C[1]_25         =   12632256
      Image_25        =   26
      ClassName_26    =   "CCWPictImage"
      Bltin_26        =   -1  'True
      Stretch_26      =   -1  'True
      Pict_26         =   1
      F_26            =   -2147483633
      B_26            =   12632256
   End
   Begin CWUIControlsLib.CWGraph CWGraph3 
      Height          =   1035
      Index           =   1
      Left            =   1200
      TabIndex        =   64
      Top             =   1560
      Width           =   8895
      _Version        =   65536
      _ExtentX        =   15690
      _ExtentY        =   1826
      _StockProps     =   68
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Small Fonts"
         Size            =   6
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Reset_0         =   0   'False
      CompatibleVers_0=   65536
      Graph_0         =   1
      ClassName_1     =   "CCWGraphFrame"
      opts_1          =   30
      C[0]_1          =   12632256
      Event_1         =   2
      ClassName_2     =   "CCWGFPlotEvent"
      Owner_2         =   1
      Plots_1         =   3
      ClassName_3     =   "CCWDataPlots"
      Array_3         =   1
      Editor_3        =   4
      ClassName_4     =   "CCWGFPlotArrayEditor"
      Owner_4         =   1
      Array[0]_3      =   5
      ClassName_5     =   "CCWDataPlot"
      opts_5          =   4194335
      Name_5          =   "Plot-1"
      C[0]_5          =   8388608
      C[1]_5          =   255
      C[2]_5          =   16711680
      C[3]_5          =   16776960
      Event_5         =   2
      X_5             =   6
      ClassName_6     =   "CCWAxis"
      opts_6          =   1567
      Name_6          =   "XAxis"
      Orientation_6   =   512
      format_6        =   7
      ClassName_7     =   "CCWFormat"
      Scale_6         =   8
      ClassName_8     =   "CCWScale"
      opts_8          =   90112
      rMin_8          =   23
      rMax_8          =   588
      dMax_8          =   10
      discInterval_8  =   1
      Radial_6        =   0
      Enum_6          =   9
      ClassName_9     =   "CCWEnum"
      Editor_9        =   10
      ClassName_10    =   "CCWEnumArrayEditor"
      Owner_10        =   6
      tickopts_6      =   2707
      major_6         =   1
      minor_6         =   0.5
      Y_5             =   11
      ClassName_11    =   "CCWAxis"
      opts_11         =   1567
      Name_11         =   "YAxis-1"
      Orientation_11  =   2067
      format_11       =   12
      ClassName_12    =   "CCWFormat"
      Scale_11        =   13
      ClassName_13    =   "CCWScale"
      opts_13         =   122880
      rMin_13         =   9
      rMax_13         =   59
      dMax_13         =   10
      discInterval_13 =   1
      Radial_11       =   0
      Enum_11         =   14
      ClassName_14    =   "CCWEnum"
      Editor_14       =   15
      ClassName_15    =   "CCWEnumArrayEditor"
      Owner_15        =   11
      tickopts_11     =   2711
      major_11        =   5
      minor_11        =   2.5
      LineStyle_5     =   1
      LineWidth_5     =   1
      BasePlot_5      =   0
      Axes_1          =   16
      ClassName_16    =   "CCWAxes"
      Array_16        =   2
      Editor_16       =   17
      ClassName_17    =   "CCWGFAxisArrayEditor"
      Owner_17        =   1
      Array[0]_16     =   6
      Array[1]_16     =   11
      DefaultPlot_1   =   18
      ClassName_18    =   "CCWDataPlot"
      opts_18         =   4194335
      Name_18         =   "[Template]"
      C[0]_18         =   65280
      C[1]_18         =   255
      C[2]_18         =   16711680
      C[3]_18         =   16776960
      Event_18        =   2
      X_18            =   6
      Y_18            =   11
      LineStyle_18    =   1
      LineWidth_18    =   1
      BasePlot_18     =   0
      Cursors_1       =   19
      ClassName_19    =   "CCWCursors"
      Array_19        =   2
      Editor_19       =   20
      ClassName_20    =   "CCWGFCursorArrayEditor"
      Owner_20        =   1
      Array[0]_19     =   21
      ClassName_21    =   "CCWCursor"
      opts_21         =   31
      Name_21         =   "Cursor-1"
      C[0]_21         =   255
      Event_21        =   2
      X_21            =   6
      Y_21            =   11
      XPos_21         =   1.05263161659241
      YPos_21         =   8.07106399536133
      SnapMode_21     =   1
      PointIndex_21   =   2
      ChrosshairStyle_21=   2
      PointStyle_21   =   3
      LockPlot_21     =   5
      Array[1]_19     =   22
      ClassName_22    =   "CCWCursor"
      opts_22         =   31
      Name_22         =   "Cursor-2"
      C[0]_22         =   65535
      Event_22        =   2
      X_22            =   6
      Y_22            =   11
      XPos_22         =   2.10526323318481
      YPos_22         =   9.84700107574463
      SnapMode_22     =   1
      PointIndex_22   =   4
      ChrosshairStyle_22=   2
      PointStyle_22   =   3
      LockPlot_22     =   5
      TrackMode_1     =   2
      GraphBackground_1=   0
      GraphFrame_1    =   23
      ClassName_23    =   "CCWDrawObj"
      opts_23         =   28
      Image_23        =   24
      ClassName_24    =   "CCWPictImage"
      Bltin_24        =   -1  'True
      Stretch_24      =   -1  'True
      F_24            =   -2147483633
      B_24            =   -2147483633
      PlotFrame_1     =   25
      ClassName_25    =   "CCWDrawObj"
      opts_25         =   30
      C[1]_25         =   12632256
      Image_25        =   26
      ClassName_26    =   "CCWPictImage"
      Bltin_26        =   -1  'True
      Stretch_26      =   -1  'True
      Pict_26         =   1
      F_26            =   -2147483633
      B_26            =   12632256
   End
   Begin MSComDlg.CommonDialog alista 
      Left            =   11280
      Top             =   2160
      _ExtentX        =   847
      _ExtentY        =   847
      _Version        =   393216
      InitDir         =   "c:\dia"
   End
   Begin MSComDlg.CommonDialog p 
      Left            =   11280
      Top             =   1500
      _ExtentX        =   847
      _ExtentY        =   847
      _Version        =   393216
      CancelError     =   -1  'True
   End
   Begin VB.CommandButton Command11 
      Caption         =   "Imprimir"
      Height          =   255
      Left            =   9360
      TabIndex        =   44
      Top             =   3720
      Width           =   735
   End
   Begin VB.CommandButton Command10 
      Caption         =   "B"
      Height          =   255
      Left            =   9720
      TabIndex        =   42
      Top             =   6840
      Width           =   255
   End
   Begin VB.CommandButton Command9 
      Caption         =   "B"
      Height          =   255
      Left            =   9720
      TabIndex        =   41
      Top             =   6480
      Width           =   255
   End
   Begin VB.CommandButton Command8 
      Caption         =   "B"
      Height          =   255
      Left            =   9720
      TabIndex        =   40
      Top             =   6120
      Width           =   255
   End
   Begin VB.VScrollBar bvx 
      Height          =   255
      Left            =   8280
      Max             =   0
      Min             =   15
      TabIndex        =   37
      Top             =   7320
      Width           =   375
   End
   Begin VB.CommandButton Command7 
      Caption         =   "Proceso"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   8760
      TabIndex        =   25
      Top             =   7200
      Width           =   1215
   End
   Begin VB.CommandButton command6 
      Caption         =   "Coda"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   8760
      TabIndex        =   24
      Top             =   6840
      Width           =   975
   End
   Begin VB.CommandButton Command5 
      Caption         =   "Fase S"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   8760
      TabIndex        =   23
      Top             =   6480
      Width           =   975
   End
   Begin VB.CommandButton Command4 
      Caption         =   "Fase P"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   8760
      TabIndex        =   22
      Top             =   6120
      Width           =   975
   End
   Begin VB.CommandButton Command3 
      Caption         =   "Zoom"
      Height          =   255
      Left            =   8160
      TabIndex        =   16
      Top             =   3960
      Width           =   1935
   End
   Begin VB.VScrollBar bv4 
      Height          =   255
      Left            =   6720
      Max             =   1
      Min             =   31
      TabIndex        =   11
      Top             =   3960
      Value           =   10
      Width           =   495
   End
   Begin VB.VScrollBar bv3 
      Height          =   255
      Left            =   4920
      Max             =   1
      Min             =   30
      TabIndex        =   10
      Top             =   3960
      Value           =   1
      Width           =   495
   End
   Begin VB.VScrollBar bv2 
      Height          =   255
      Left            =   3120
      Max             =   1
      Min             =   9
      TabIndex        =   9
      Top             =   3960
      Value           =   1
      Width           =   495
   End
   Begin VB.VScrollBar bv1 
      Height          =   255
      Left            =   6960
      Max             =   0
      Min             =   15
      TabIndex        =   7
      Top             =   3720
      Width           =   255
   End
   Begin VB.CommandButton Command2 
      BackColor       =   &H000000FF&
      Caption         =   "Filtrar"
      Height          =   255
      Left            =   7200
      TabIndex        =   2
      Top             =   3960
      Width           =   975
   End
   Begin VB.CommandButton Command1 
      Caption         =   "Dibujar"
      Height          =   255
      Left            =   7200
      TabIndex        =   0
      Top             =   3720
      Width           =   1635
   End
   Begin MSComDlg.CommonDialog a 
      Left            =   11280
      Top             =   840
      _ExtentX        =   847
      _ExtentY        =   847
      _Version        =   393216
      DialogTitle     =   "Sismo"
      Filter          =   "Sismo *.sis|*.sis|"
      InitDir         =   "c:\dia"
   End
   Begin CWUIControlsLib.CWGraph CWGraph2 
      Height          =   3135
      Left            =   1200
      TabIndex        =   15
      Top             =   4200
      Width           =   7455
      _Version        =   65536
      _ExtentX        =   13150
      _ExtentY        =   5530
      _StockProps     =   68
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Reset_0         =   0   'False
      CompatibleVers_0=   65536
      Graph_0         =   1
      ClassName_1     =   "CCWGraphFrame"
      opts_1          =   30
      C[0]_1          =   12632256
      Event_1         =   2
      ClassName_2     =   "CCWGFPlotEvent"
      Owner_2         =   1
      Plots_1         =   3
      ClassName_3     =   "CCWDataPlots"
      Array_3         =   1
      Editor_3        =   4
      ClassName_4     =   "CCWGFPlotArrayEditor"
      Owner_4         =   1
      Array[0]_3      =   5
      ClassName_5     =   "CCWDataPlot"
      opts_5          =   4194335
      Name_5          =   "Plot-1"
      C[0]_5          =   8388608
      C[1]_5          =   255
      C[2]_5          =   16711680
      C[3]_5          =   16776960
      Event_5         =   2
      X_5             =   6
      ClassName_6     =   "CCWAxis"
      opts_6          =   1567
      Name_6          =   "XAxis"
      Orientation_6   =   2944
      format_6        =   7
      ClassName_7     =   "CCWFormat"
      Scale_6         =   8
      ClassName_8     =   "CCWScale"
      opts_8          =   90112
      rMin_8          =   25
      rMax_8          =   486
      dMax_8          =   10
      discInterval_8  =   1
      Radial_6        =   0
      Enum_6          =   9
      ClassName_9     =   "CCWEnum"
      Editor_9        =   10
      ClassName_10    =   "CCWEnumArrayEditor"
      Owner_10        =   6
      tickopts_6      =   2711
      major_6         =   1
      minor_6         =   0.5
      Y_5             =   11
      ClassName_11    =   "CCWAxis"
      opts_11         =   1567
      Name_11         =   "YAxis-1"
      Orientation_11  =   2067
      format_11       =   12
      ClassName_12    =   "CCWFormat"
      Scale_11        =   13
      ClassName_13    =   "CCWScale"
      opts_13         =   122880
      rMin_13         =   10
      rMax_13         =   182
      dMax_13         =   10
      discInterval_13 =   1
      Radial_11       =   0
      Enum_11         =   14
      ClassName_14    =   "CCWEnum"
      Editor_14       =   15
      ClassName_15    =   "CCWEnumArrayEditor"
      Owner_15        =   11
      tickopts_11     =   2711
      major_11        =   2
      minor_11        =   1
      LineStyle_5     =   1
      LineWidth_5     =   1
      BasePlot_5      =   0
      Axes_1          =   16
      ClassName_16    =   "CCWAxes"
      Array_16        =   2
      Editor_16       =   17
      ClassName_17    =   "CCWGFAxisArrayEditor"
      Owner_17        =   1
      Array[0]_16     =   6
      Array[1]_16     =   11
      DefaultPlot_1   =   18
      ClassName_18    =   "CCWDataPlot"
      opts_18         =   4194335
      Name_18         =   "[Template]"
      C[0]_18         =   65280
      C[1]_18         =   255
      C[2]_18         =   16711680
      C[3]_18         =   16776960
      Event_18        =   2
      X_18            =   6
      Y_18            =   11
      LineStyle_18    =   1
      LineWidth_18    =   1
      BasePlot_18     =   0
      Cursors_1       =   19
      ClassName_19    =   "CCWCursors"
      Array_19        =   1
      Editor_19       =   20
      ClassName_20    =   "CCWGFCursorArrayEditor"
      Owner_20        =   1
      Array[0]_19     =   21
      ClassName_21    =   "CCWCursor"
      opts_21         =   31
      Name_21         =   "Cursor-1"
      C[0]_21         =   16776960
      Event_21        =   2
      X_21            =   6
      Y_21            =   11
      XPos_21         =   1
      YPos_21         =   1
      PointIndex_21   =   -1
      ChrosshairStyle_21=   2
      PointStyle_21   =   18
      LockPlot_21     =   5
      TrackMode_1     =   2
      GraphBackground_1=   0
      GraphFrame_1    =   22
      ClassName_22    =   "CCWDrawObj"
      opts_22         =   30
      Image_22        =   23
      ClassName_23    =   "CCWPictImage"
      Bltin_23        =   -1  'True
      Stretch_23      =   -1  'True
      F_23            =   -2147483633
      B_23            =   -2147483633
      PlotFrame_1     =   24
      ClassName_24    =   "CCWDrawObj"
      opts_24         =   30
      C[1]_24         =   12632256
      Image_24        =   25
      ClassName_25    =   "CCWPictImage"
      Bltin_25        =   -1  'True
      Stretch_25      =   -1  'True
      Pict_25         =   1
      F_25            =   -2147483633
      B_25            =   12632256
   End
   Begin CWUIControlsLib.CWGraph CWGraph1 
      Height          =   3135
      Left            =   1200
      TabIndex        =   1
      Top             =   600
      Width           =   8895
      _Version        =   65536
      _ExtentX        =   15690
      _ExtentY        =   5530
      _StockProps     =   68
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Reset_0         =   0   'False
      CompatibleVers_0=   65536
      Graph_0         =   1
      ClassName_1     =   "CCWGraphFrame"
      opts_1          =   30
      C[0]_1          =   12632256
      Event_1         =   2
      ClassName_2     =   "CCWGFPlotEvent"
      Owner_2         =   1
      Plots_1         =   3
      ClassName_3     =   "CCWDataPlots"
      Array_3         =   1
      Editor_3        =   4
      ClassName_4     =   "CCWGFPlotArrayEditor"
      Owner_4         =   1
      Array[0]_3      =   5
      ClassName_5     =   "CCWDataPlot"
      opts_5          =   4194335
      Name_5          =   "Plot-1"
      C[0]_5          =   8388608
      C[1]_5          =   255
      C[2]_5          =   16711680
      C[3]_5          =   16776960
      Event_5         =   2
      X_5             =   6
      ClassName_6     =   "CCWAxis"
      opts_6          =   1567
      Name_6          =   "XAxis"
      Orientation_6   =   2944
      format_6        =   7
      ClassName_7     =   "CCWFormat"
      Format_7        =   "*0.015625"
      Scale_6         =   8
      ClassName_8     =   "CCWScale"
      opts_8          =   90112
      rMin_8          =   25
      rMax_8          =   569
      dMax_8          =   10
      discInterval_8  =   1
      Radial_6        =   0
      Enum_6          =   9
      ClassName_9     =   "CCWEnum"
      Editor_9        =   10
      ClassName_10    =   "CCWEnumArrayEditor"
      Owner_10        =   6
      tickopts_6      =   2711
      major_6         =   2
      minor_6         =   1
      Y_5             =   11
      ClassName_11    =   "CCWAxis"
      opts_11         =   1567
      Name_11         =   "YAxis-1"
      Orientation_11  =   2067
      format_11       =   12
      ClassName_12    =   "CCWFormat"
      Scale_11        =   13
      ClassName_13    =   "CCWScale"
      opts_13         =   122880
      rMin_13         =   10
      rMax_13         =   182
      dMax_13         =   10
      discInterval_13 =   1
      Radial_11       =   0
      Enum_11         =   14
      ClassName_14    =   "CCWEnum"
      Editor_14       =   15
      ClassName_15    =   "CCWEnumArrayEditor"
      Owner_15        =   11
      tickopts_11     =   2711
      major_11        =   2
      minor_11        =   1
      LineStyle_5     =   1
      LineWidth_5     =   1
      BasePlot_5      =   0
      Axes_1          =   16
      ClassName_16    =   "CCWAxes"
      Array_16        =   2
      Editor_16       =   17
      ClassName_17    =   "CCWGFAxisArrayEditor"
      Owner_17        =   1
      Array[0]_16     =   6
      Array[1]_16     =   11
      DefaultPlot_1   =   18
      ClassName_18    =   "CCWDataPlot"
      opts_18         =   4194335
      Name_18         =   "[Template]"
      C[0]_18         =   65280
      C[1]_18         =   255
      C[2]_18         =   16711680
      C[3]_18         =   16776960
      Event_18        =   2
      X_18            =   6
      Y_18            =   11
      LineStyle_18    =   1
      LineWidth_18    =   1
      BasePlot_18     =   0
      Cursors_1       =   19
      ClassName_19    =   "CCWCursors"
      Array_19        =   3
      Editor_19       =   20
      ClassName_20    =   "CCWGFCursorArrayEditor"
      Owner_20        =   1
      Array[0]_19     =   21
      ClassName_21    =   "CCWCursor"
      opts_21         =   31
      Name_21         =   "Cursor-1"
      C[0]_21         =   255
      Event_21        =   2
      X_21            =   6
      Y_21            =   11
      XPos_21         =   1
      YPos_21         =   1
      SnapMode_21     =   2
      PointIndex_21   =   -1
      ChrosshairStyle_21=   2
      PointStyle_21   =   3
      LockPlot_21     =   5
      Array[1]_19     =   22
      ClassName_22    =   "CCWCursor"
      opts_22         =   31
      Name_22         =   "Cursor-2"
      C[0]_22         =   65535
      Event_22        =   2
      X_22            =   6
      Y_22            =   11
      XPos_22         =   2
      YPos_22         =   2
      SnapMode_22     =   2
      PointIndex_22   =   -1
      ChrosshairStyle_22=   2
      PointStyle_22   =   3
      LockPlot_22     =   5
      Array[2]_19     =   23
      ClassName_23    =   "CCWCursor"
      opts_23         =   31
      Name_23         =   "Cursor-3"
      C[0]_23         =   65280
      Event_23        =   2
      X_23            =   6
      Y_23            =   11
      XPos_23         =   4.21052646636963
      YPos_23         =   7.37973690032959
      SnapMode_23     =   1
      PointIndex_23   =   8
      ChrosshairStyle_23=   2
      PointStyle_23   =   12
      LockPlot_23     =   5
      TrackMode_1     =   2
      GraphBackground_1=   0
      GraphFrame_1    =   24
      ClassName_24    =   "CCWDrawObj"
      opts_24         =   30
      Image_24        =   25
      ClassName_25    =   "CCWPictImage"
      Bltin_25        =   -1  'True
      Stretch_25      =   -1  'True
      F_25            =   -2147483633
      B_25            =   -2147483633
      PlotFrame_1     =   26
      ClassName_26    =   "CCWDrawObj"
      opts_26         =   30
      C[1]_26         =   12632256
      Image_26        =   27
      ClassName_27    =   "CCWPictImage"
      Bltin_27        =   -1  'True
      Stretch_27      =   -1  'True
      Pict_27         =   1
      F_27            =   -2147483633
      B_27            =   12632256
   End
   Begin VB.Label Label28 
      Alignment       =   2  'Center
      BackColor       =   &H00C0E0FF&
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H000000FF&
      Height          =   255
      Left            =   10140
      TabIndex        =   62
      Top             =   600
      Width           =   735
   End
   Begin VB.Label Label14 
      AutoSize        =   -1  'True
      BackColor       =   &H00808080&
      Caption         =   "Escoja un archivo!"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   240
      Left            =   1200
      TabIndex        =   39
      Top             =   240
      Width           =   1920
   End
   Begin VB.Shape Shape9 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   975
      Left            =   8640
      Top             =   6120
      Width           =   135
   End
   Begin VB.Label Label13 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Height          =   255
      Left            =   8040
      TabIndex        =   38
      Top             =   7320
      Width           =   255
   End
   Begin VB.Shape Shape8 
      BorderColor     =   &H00C0C0C0&
      BorderWidth     =   3
      Height          =   6975
      Left            =   1200
      Top             =   600
      Width           =   8895
   End
   Begin VB.Label Label27 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "N"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9600
      TabIndex        =   36
      Top             =   5760
      Width           =   495
   End
   Begin VB.Label Label26 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "--"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9120
      TabIndex        =   35
      Top             =   5760
      Width           =   495
   End
   Begin VB.Label Label25 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "+"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   8640
      TabIndex        =   34
      Top             =   5760
      Width           =   495
   End
   Begin VB.Label Label24 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "N"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9600
      TabIndex        =   33
      Top             =   5040
      Width           =   495
   End
   Begin VB.Label Label23 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "E"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9120
      TabIndex        =   32
      Top             =   5040
      Width           =   495
   End
   Begin VB.Label Label22 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "I"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   11.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   8640
      TabIndex        =   31
      Top             =   5040
      Width           =   495
   End
   Begin VB.Label Label21 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "4"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9840
      TabIndex        =   30
      Top             =   5400
      Width           =   255
   End
   Begin VB.Label Label20 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "3"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9600
      TabIndex        =   29
      Top             =   5400
      Width           =   255
   End
   Begin VB.Label Label19 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "2"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9360
      TabIndex        =   28
      Top             =   5400
      Width           =   255
   End
   Begin VB.Label Label18 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "1"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   9120
      TabIndex        =   27
      Top             =   5400
      Width           =   255
   End
   Begin VB.Label Label17 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "P. :0"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   8640
      TabIndex        =   26
      Top             =   5400
      Width           =   495
   End
   Begin VB.Shape Shape7 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   7080
      Width           =   1455
   End
   Begin VB.Shape Shape6 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   6720
      Width           =   1455
   End
   Begin VB.Shape Shape5 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   6360
      Width           =   1455
   End
   Begin VB.Shape Shape4 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   6000
      Width           =   1455
   End
   Begin VB.Shape Shape3 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   5640
      Width           =   1455
   End
   Begin VB.Label Label15 
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "  FASES DEL SISMO:"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FF0000&
      Height          =   255
      Left            =   1200
      TabIndex        =   21
      Top             =   7320
      Width           =   6855
   End
   Begin VB.Shape Shape2 
      BackColor       =   &H00000000&
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   4920
      Width           =   1455
   End
   Begin VB.Shape Shape1 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   5280
      Width           =   1455
   End
   Begin VB.Label Label12 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "Dirección"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   8640
      TabIndex        =   20
      Top             =   4680
      Width           =   1455
   End
   Begin VB.Label Label11 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "Tiempo"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   255
      Left            =   8640
      TabIndex        =   19
      Top             =   4440
      Width           =   1455
   End
   Begin VB.Label Label10 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "Hora local"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFF00&
      Height          =   255
      Left            =   8640
      TabIndex        =   18
      Top             =   4200
      Width           =   1455
   End
   Begin VB.Label Label9 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Butterworth"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00800000&
      Height          =   255
      Left            =   1200
      TabIndex        =   17
      Top             =   3960
      Width           =   1215
   End
   Begin VB.Label Label8 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Freq.Sup(Hz):10"
      Height          =   255
      Left            =   5400
      TabIndex        =   14
      Top             =   3960
      Width           =   1335
   End
   Begin VB.Label Label7 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Freq.Inf(Hz) =1"
      Height          =   255
      Left            =   3600
      TabIndex        =   13
      Top             =   3960
      Width           =   1335
   End
   Begin VB.Label Label6 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Orden:1"
      Height          =   255
      Left            =   2400
      TabIndex        =   12
      Top             =   3960
      Width           =   735
   End
   Begin VB.Label Label5 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Plot:0"
      Height          =   255
      Left            =   6000
      TabIndex        =   8
      Top             =   3720
      Width           =   975
   End
   Begin VB.Label Label4 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Height          =   255
      Left            =   4800
      TabIndex        =   6
      Top             =   3720
      Width           =   1215
   End
   Begin VB.Label Label3 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Height          =   255
      Left            =   3600
      TabIndex        =   5
      Top             =   3720
      Width           =   1215
   End
   Begin VB.Label Label2 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      ForeColor       =   &H00000000&
      Height          =   255
      Left            =   2400
      TabIndex        =   4
      Top             =   3720
      Width           =   1215
   End
   Begin VB.Label Label1 
      Alignment       =   2  'Center
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Height          =   255
      Left            =   1200
      TabIndex        =   3
      Top             =   3720
      Width           =   1215
   End
   Begin CWAnalysisKey.CWAnalysisKey CWAnalysisKey1 
      Left            =   11280
      Top             =   120
      _Version        =   65536
      _ExtentX        =   847
      _ExtentY        =   847
      _StockProps     =   0
   End
   Begin VB.Shape Shape10 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   975
      Left            =   9960
      Top             =   6120
      Width           =   135
   End
   Begin VB.Shape Shape11 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   375
      Left            =   9960
      Top             =   7200
      Width           =   135
   End
   Begin VB.Shape Shape12 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   375
      Left            =   8640
      Top             =   7200
      Width           =   135
   End
   Begin VB.Shape Shape13 
      BackStyle       =   1  'Opaque
      FillStyle       =   0  'Solid
      Height          =   135
      Left            =   8640
      Top             =   7440
      Width           =   1455
   End
   Begin VB.Label Label16 
      AutoSize        =   -1  'True
      BackColor       =   &H00808080&
      Caption         =   "Programado por: Ing. Jorge Cabrera A."
      ForeColor       =   &H0000C000&
      Height          =   195
      Left            =   7560
      TabIndex        =   43
      Top             =   360
      Width           =   2715
   End
   Begin VB.Menu archivo 
      Caption         =   "&Archivo"
      Begin VB.Menu abrir 
         Caption         =   "A&brir"
         Shortcut        =   ^A
      End
      Begin VB.Menu cerrar 
         Caption         =   "&Cerrar"
         Shortcut        =   ^X
      End
      Begin VB.Menu salir 
         Caption         =   "&Salir"
         Shortcut        =   ^F
      End
   End
   Begin VB.Menu inf 
      Caption         =   "&Información"
      Enabled         =   0   'False
   End
   Begin VB.Menu gra 
      Caption         =   "Archivo grafico (.BLN)"
      Enabled         =   0   'False
   End
   Begin VB.Menu da 
      Caption         =   "Archivo de datos (.DAT)"
      Enabled         =   0   'False
   End
   Begin VB.Menu dac 
      Caption         =   "Datos complementarios"
      Enabled         =   0   'False
   End
   Begin VB.Menu ims 
      Caption         =   "Imprimir serie"
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Dim k() As Double
Dim X() As Double
Dim Y() As Double
Dim z() As Double
Dim s() As Double
Dim qw As String
Dim fs, fl, fh As Double
Dim i As Integer
Dim px1, px2 As Integer
Dim order, status As Long
Dim ba1 As Integer
Dim tiempo As Variant
Dim ll As Integer
Dim est(15) As String
Dim ud As Integer
Dim tf As Single
Dim fas(15, 7) As Variant
Dim pes As Integer
Dim ien As Integer
Dim mmm As Variant
Dim ccc As Variant
Dim ttt As Variant
Dim vvv As Variant
Dim fec As Variant
Dim cab() As Variant
Dim fca As Variant
Dim ma As Double
Dim ima As Long
Dim mi As Double
Dim imi As Long
Dim das As String
Dim li(999, 1) As String
Dim qwx As String
Dim rh As Double
Dim rm As Double
Dim rs As Double
Dim ptresc() As Integer
Dim ntresc As Integer
Dim itresc As Integer
Dim cheche(15) As Integer

Function imprimir(vv, ma, mi, ind, l, h)

Printer.Line (2, ind)-(19, ind + 3.5), , B
uy = 3.5 / (ma + Abs(mi))
ux = 17 / l
i = 0
Printer.Line (2, ind + ma * uy - vv(i) * uy)-(2, ind + ma * uy - vv(i) * uy)
For i = 1 To l - 1
Printer.Line -(2 + ux * i, ind + ma * uy - vv(i) * uy)
Next
''labels
For i = 0 To l - 1 Step 64 * 10
Printer.Line (2 + ux * i, ind + 3.5)-(2 + ux * i, ind + 3.5 + 0.2)
Printer.Print i / 64
Next

Printer.Line (1.8, ind + ma * uy)-(1.8, ind + ma * uy)
Printer.Print "0"
Printer.Line (1.8, ind + ma * uy)-(2, ind + ma * uy)
Printer.Line (2, ind - 0.3)-(2, ind - 0.3)
Printer.Print "ESTACION : " + h
Printer.Line (10, ind + 4)-(10, ind + 4)
Printer.Print "segundos"

End Function


Function rotulo()
Printer.FontSize = 14
Printer.Line (7, 1.5)-(7, 1.5)
Printer.Print "RED SISMICA DEL AUSTRO"
Printer.Line (7, 2)-(7, 2)
Printer.Print "    REGISTRO SISMICO"
Printer.Line (3, 2.5)-(3, 2.5)
Printer.Print "FECHA: " + fec + "                                        HORA GMT: " + Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")
Printer.Line (3, 3)-(3, 3)
Printer.FontSize = 12
Printer.Print "Localización: " + das
Printer.FontSize = 10
Printer.Line (2, 3.5)-(2, 3.5)
Printer.Print "Mustras/seg: " + Format(mmm, "#") + "   Canales: " + Format(ccc, "#") + "   Tarjeta A/D: " + Format(ttt, "#") + "   Programa : " + Format(vvv, "#")
Printer.FontSize = 5
tpp = 4
For i = 0 To ccc
lef = 2
For j = 0 To 8
Printer.Line (lef, tpp)-(lef, tpp)
Printer.Print cabe(i, j)
lef = lef + 1.5
Next
tpp = tpp + 0.15
Next


End Function

Private Sub bv1_Change()
Label5.Caption = "Plot:" + Str$(bv1.Value)

Label24.ForeColor = QBColor(12)
Label22.ForeColor = QBColor(10)
Label23.ForeColor = QBColor(10)
ien = 2
Label17.ForeColor = QBColor(12)
Label18.ForeColor = QBColor(10)
Label19.ForeColor = QBColor(10)
Label20.ForeColor = QBColor(10)
Label21.ForeColor = QBColor(10)
pes = 0
Label27.ForeColor = QBColor(12)
Label25.ForeColor = QBColor(10)
Label26.ForeColor = QBColor(10)
ud = 4
Command2.Enabled = False
Command3.Enabled = False
CWGraph2.ClearData
Label15.Caption = est(bv1.Value)
Command12.Enabled = False
Command13.Enabled = False
Command14.Enabled = False

Command4.Enabled = False
Command5.Enabled = False
command6.Enabled = False
Command7.Enabled = False
Command8.Enabled = False
Command9.Enabled = False
Command10.Enabled = False

End Sub


Private Sub bv2_Change()
order = bv2.Value
Label6.Caption = "Orden:" + Str$(bv2.Value)
Command2.Default = True
End Sub

Private Sub bv3_Change()
fl = bv3.Value
bv4.Max = bv3.Value + 1
Label7.Caption = "Freq.Inf(Hz):" + Str$(bv3.Value)
End Sub

Private Sub bv4_Change()
fh = bv4.Value
Label8.Caption = "Freq.Sup(Hz):" + Str$(bv4.Value)
End Sub




Private Sub bvx_Change()
Label13.Caption = bvx.Value
i = bvx.Value
Label15.Caption = "FASE P: " + fas(i, 2) + "  FASE S: " + fas(i, 5) + "  CODA: " + fas(i, 7)
End Sub

Private Sub cerrar_Click()

Close
Label14.Caption = "Escoja un archivo!"
abrir.Enabled = True
abrir.Checked = False
Command1.Enabled = False
Command2.Enabled = False
Command3.Enabled = False
Command11.Enabled = False

For w = 0 To 15
fas(w, 2) = "                        "
fas(w, 5) = "         "
fas(w, 7) = "    "
fas(w, 0) = 0
Next
CWGraph1.ClearData
CWGraph2.ClearData
inf.Enabled = False
gra.Enabled = False
da.Enabled = False
dac.Enabled = False
das = ""
CWGraph3(0).Visible = False
CWGraph3(1).Visible = False
CWGraph3(2).Visible = False
CWGraph1.Visible = True
Label28.Caption = ""

Command12.Enabled = False
Command13.Enabled = False
Command14.Enabled = False

Command4.Enabled = False
Command5.Enabled = False
command6.Enabled = False
Command7.Enabled = False
Command8.Enabled = False
Command9.Enabled = False
Command10.Enabled = False

For i = 0 To 15
Check1(i).Value = 0
Next

End Sub

Private Sub Command1_Click()
On Error GoTo rutinae

Command12.Enabled = True
Command13.Enabled = True
Command14.Enabled = True

ntresc = 0

For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
ntresc = ntresc + 1
End If
Next
ReDim ptresc(ntresc - 1) As Integer
j = 0
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
ptresc(j) = i
j = j + 1
End If
Next


If ntresc > 1 Then
Label28.Visible = True
CWGraph1.Visible = False
    If ntresc = 2 Then
    CWGraph3(0).Visible = True
    CWGraph3(1).Visible = True
    CWGraph3(2).ClearData
    CWGraph3(2).Visible = True
For pli = 0 To 1

Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")

l = FileLen(a.filename)
l = (l - 8 - fca) / (2068)
ll = l

ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(ptresc(pli), j)
i = i + 1
Next
Next

CWGraph3(pli).PlotY X
Seek #1, fca
ba1 = 1
Label6.BackColor = QBColor(15)
Label7.BackColor = QBColor(15)
Label8.BackColor = QBColor(15)
Command2.Enabled = True
Command3.Enabled = True
Label15.Caption = est(bv1.Value)
gra.Enabled = False
da.Enabled = True

Next

    End If
    If ntresc = 3 Then
    CWGraph3(0).Visible = True
    CWGraph3(1).Visible = True
    CWGraph3(2).Visible = True
    
For pli = 0 To 2

Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")

l = FileLen(a.filename)
l = (l - 8 - fca) / (2068)
ll = l

ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(ptresc(pli), j)
i = i + 1
Next
Next

CWGraph3(pli).PlotY X
Seek #1, fca
ba1 = 1
Label6.BackColor = QBColor(15)
Label7.BackColor = QBColor(15)
Label8.BackColor = QBColor(15)
Command2.Enabled = True
Command3.Enabled = True
Label15.Caption = est(bv1.Value)
gra.Enabled = False
da.Enabled = True

Next
    
    End If
Else
CWGraph1.Visible = True
CWGraph3(0).Visible = False
CWGraph3(1).Visible = False
CWGraph3(2).Visible = False
End If

''normal
If ntresc = 1 Then
Label28.Visible = False
Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")

l = FileLen(a.filename)
l = (l - 8 - fca) / (2068)
ll = l

ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(bv1.Value, j)
i = i + 1
Next
Next

CWGraph1.PlotY X
Seek #1, fca
ba1 = 1
Label6.BackColor = QBColor(15)
Label7.BackColor = QBColor(15)
Label8.BackColor = QBColor(15)
Command2.Enabled = True
Command3.Enabled = True
Label15.Caption = est(bv1.Value)
gra.Enabled = False
da.Enabled = True

End If

Command7.Enabled = True

salir:
Exit Sub

rutinae:
GoTo salir

End Sub

Private Sub abrir_Click()
Dim rpha As String

a.Action = 1
If a.filename = "" Then
MsgBox "No escogio ningun sismo", 16, "Alto"
Else

For i = 0 To 15
Check1(i).Value = 0
Next

qw = a.filename
qw = Mid$(qw, (Len(qw)) - 15, 12)
Open a.filename For Binary Access Read As #1
Get #1, , mmm
Get #1, , ccc
Get #1, , ttt
Get #1, , vvv
Get #1, , fec
ReDim cab(ccc, 8) As Variant
ReDim cabe(ccc, 8) As Variant

For i = 0 To ccc
For j = 0 To 8
Get #1, , cab(i, j)
cabe(i, j) = cab(i, j)
Next
Next
fca = Seek(1)

For i = 0 To 15
est(i) = cab(i + 1, 2)
Next

Label14.Caption = a.filename
abrir.Enabled = False
abrir.Checked = True
Command1.Enabled = True
inf.Enabled = True
dac.Enabled = True
Command11.Enabled = True
For i = 0 To 15
Check1(i).Value = cab(i + 1, 1)
Next

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
If Dir(rpha) <> "" Then
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Get #5, , fas(i, j)
Next
Next
Close #5
End If

End If

End Sub

Private Sub Command10_Click()
Dim rpha As String

If ntresc = 1 Then
fas(bv1.Value, 6) = 0
fas(bv1.Value, 7) = "    "
End If
If ntresc > 1 Then
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(bv1.Value, 6) = 0
fas(i, 7) = "    "
End If
Next
End If

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5

End Sub

Private Sub Command11_Click()
On Error GoTo rutinae
p.Action = 5
Printer.FontName = "courier"
Printer.FontBold = False
Printer.FontSize = 6
''Form3.Enabled = True
''Form3.Show
''Form3.Scale (0, 0)-(21, 29.7)
Printer.Scale (0, 0)-(21, 29.7)
Printer.FontName = "Arial"
Printer.FontBold = True
Printer.FontSize = 7

ing = 7
cnp = 0
cnpi = 0

For sv = 0 To 15
If Check1(sv).Value = 1 Then
cnpi = cnpi + 1
End If
Next

For sv = 0 To 15
If Check1(sv).Value = 1 Then
Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")
l = FileLen(a.filename)
l = (l - 8 - fca) / 2068
ll = l
ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(sv, j)
i = i + 1
Next
Next
status = MaxMin1D(X, ma, ima, mi, imi)
Seek #1, fca
nd = l * 64
Call imprimir(X, ma, mi, ing, nd, est(sv))
ing = ing + 4.5
cnp = cnp + 1
End If

If cnp = 5 And cnp < cnpi Then
Call rotulo
cnp = 0
Printer.NewPage
ing = 7
End If

Next

Call rotulo



''correcciones manuales
''Printer.Line (11, 4.9)-(11, 4.9)
''Printer.Print " 54"
''Printer.Line (11, 5.2)-(11, 5.2)
''Printer.Print " 60"
''Printer.Line (11, 5.5)-(11, 5.5)
''Printer.Print " 66"
''Printer.Line (11, 5.8)-(11, 5.8)
''Printer.Print " 54"
''Printer.Line (11, 6.1)-(11, 6.1)
''Printer.Print " 66"
''Printer.Line (6.5, 4.3)-(6.5, 4.3)
''Printer.Print "-79.02"
''Printer.Line (6.5, 4.6)-(6.5, 4.6)
''Printer.Print "-79.04"
''Printer.Line (8, 4.3)-(8, 4.3)
''Printer.Print "-2.68"
''Printer.Line (8, 4.6)-(8, 4.6)
''Printer.Print "-2.67"
''Printer.Line (9.5, 4.3)-(9.5, 4.3)
''Printer.Print " 3700"
''Printer.Line (9.5, 4.6)-(9.5, 4.6)
''Printer.Print " 3650"
''Printer.Line (11, 4.3)-(11, 4.3)
''Printer.Print "___"
''Printer.Line (11, 4.6)-(11, 4.6)
''Printer.Print "___"
''Printer.Line (12.5, 4.3)-(12.5, 4.3)
''Printer.Print "___"
''Printer.Line (12.5, 4.6)-(12.5, 4.6)
''Printer.Print "___"

Printer.EndDoc
salir:
Exit Sub

rutinae:
Resume salir


End Sub

Private Sub Command12_Click()
On Error GoTo rutinae

Dim rpha As String
Dim dti As Integer

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
If Dir(rpha) <> "" Then
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Get #5, , fas(i, j)
Next
Next
Close #5

If (Val(fas(bv1.Value, 1)) - tiempo) >= 0 Then
dti = (Val(fas(bv1.Value, 1)) - tiempo) * 64
If ntresc = 1 Then
CWGraph1.Cursors.Item(3).PointIndex = dti
End If
If ntresc > 1 Then
CWGraph3(0).Cursors.Item(3).PointIndex = dti
End If
End If
End If

salir:
Exit Sub

rutinae:
GoTo salir

End Sub

Private Sub Command13_Click()
On Error GoTo rutinae

Dim rhs As Double
Dim rms As Double
Dim rss As Double

Dim rpha As String
Dim dti As Integer

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
If Dir(rpha) <> "" Then
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Get #5, , fas(i, j)
Next
Next
Close #5


If Val(fas(bv1.Value, 4)) > 0 Then
rhs = (Val(fas(bv1.Value, 1))) / 3600
rms = 60 * (rhs - Int(rhs))
rss = 60 * (rms - Int(rms))
dti = (Val(fas(bv1.Value, 4)) + Val(fas(bv1.Value, 1)) - rss - tiempo) * 64
If ntresc = 1 Then
CWGraph1.Cursors.Item(3).PointIndex = dti
End If
If ntresc > 1 Then
CWGraph3(0).Cursors.Item(3).PointIndex = dti
End If
End If
End If

salir:
Exit Sub

rutinae:
GoTo salir

End Sub


Private Sub Command14_Click()
On Error GoTo rutinae

Dim rpha As String
Dim dti As Integer

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
If Dir(rpha) <> "" Then
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Get #5, , fas(i, j)
Next
Next
Close #5

If Val(fas(bv1.Value, 7)) > 0 Then
dti = (Val(fas(bv1.Value, 7)) + Val(fas(bv1.Value, 1)) - tiempo) * 64
If ntresc = 1 Then
CWGraph1.Cursors.Item(3).PointIndex = dti
End If
If ntresc > 1 Then
CWGraph3(0).Cursors.Item(3).PointIndex = dti
End If
End If
End If

salir:
Exit Sub

rutinae:
GoTo salir

End Sub


Private Sub Command2_Click()

If ntresc > 1 And itresc <> 4 Then
Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")

l = FileLen(a.filename)
l = (l - 8 - fca) / (2068)
ll = l

ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(ptresc(itresc), j)
i = i + 1
Next
Next
Seek #1, fca
status = Bw_BPF(X, fs, fl, fh, order, Y)
CWGraph3(itresc).PlotY Y
ba1 = 2
Label6.BackColor = QBColor(14)
Label7.BackColor = QBColor(14)
Label8.BackColor = QBColor(14)
gra.Enabled = True
End If

If ntresc = 1 Then
status = Bw_BPF(X, fs, fl, fh, order, Y)
CWGraph1.PlotY Y
ba1 = 2
Label6.BackColor = QBColor(14)
Label7.BackColor = QBColor(14)
Label8.BackColor = QBColor(14)
gra.Enabled = True
End If

End Sub


Private Sub Command3_Click()
If (px2 - px1) <= 0 Then
    GoTo salir
End If
ReDim z(px2 - px1) As Double

Label15.Caption = est(bv1.Value)

If ntresc > 1 And itresc <> 4 Then
m = 0
If ba1 = 1 Then
Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")
l = FileLen(a.filename)
l = (l - 8 - fca) / (2068)
ll = l
ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(ptresc(itresc), j)
i = i + 1
Next
Next
Seek #1, fca
For r = px1 To px2
z(m) = X(r)
m = m + 1
Next
CWGraph2.PlotY z
End If

If ba1 = 2 Then
Get #1, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label10.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(CInt(rs), "00")
l = FileLen(a.filename)
l = (l - 8 - fca) / (2068)
ll = l
ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #1, , datos
For j = 0 To 63
X(i) = datos(ptresc(itresc), j)
i = i + 1
Next
Next
Seek #1, fca
status = Bw_BPF(X, fs, fl, fh, order, Y)
For r = px1 To px2
z(m) = Y(r)
m = m + 1
Next
CWGraph2.PlotY z
End If
End If

If ntresc = 1 Then
m = 0
If ba1 = 1 Then
For r = px1 To px2
z(m) = X(r)
m = m + 1
Next
CWGraph2.PlotY z
End If

If ba1 = 2 Then
For r = px1 To px2
z(m) = Y(r)
m = m + 1
Next
CWGraph2.PlotY z
End If
End If
Command4.Enabled = True
Command5.Enabled = True
command6.Enabled = True
Command8.Enabled = True
Command9.Enabled = True
Command10.Enabled = True

salir:
End Sub

Private Sub Command4_Click()
Dim rpha As String

Select Case ien
Case Is = 0
ie = "I"
Case Is = 1
ie = "E"
Case Is = 2
ie = " "
End Select

Select Case ud
Case Is = 0
udf = "U"
Case Is = 1
udf = "D"
Case Is = 2
udf = "+"
Case Is = 3
udf = "-"
Case Is = 4
udf = " "
End Select

Select Case pes
Case Is = 0
pe = "0"
Case Is = 1
pe = "1"
Case Is = 2
pe = "2"
Case Is = 3
pe = "3"
Case Is = 4
pe = "4"
End Select

If ntresc = 1 Then
rh = tf / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
fp = Format(Int(rh), "00") + Format(Int(rm), "00") + Format(rs, "00.00")
Label15.Caption = est(bv1.Value) + ie + "P" + udf + pe + " " + Mid(a.filename, Len(CurDir()) + 2, 6) + fp
fas(bv1.Value, 0) = 1
fas(bv1.Value, 1) = tf
fas(bv1.Value, 2) = est(bv1.Value) + ie + "P" + udf + pe + " " + Mid(a.filename, Len(CurDir()) + 2, 6) + fp
End If

If ntresc > 1 Then
rh = tf / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
fp = Format(Int(rh), "00") + Format(Int(rm), "00") + Format(rs, "00.00")
Label15.Caption = est(bv1.Value) + ie + "P" + udf + pe + " " + Mid(a.filename, Len(CurDir()) + 2, 6) + fp
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(i, 0) = 1
fas(i, 1) = tf
fas(i, 2) = est(i) + ie + "P" + udf + pe + " " + Mid(a.filename, Len(CurDir()) + 2, 6) + fp
End If
Next
End If

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5

End Sub

Private Sub Command5_Click()
Dim rpha As String

If fas(bv1.Value, 0) = 1 Then

rh = (fas(bv1.Value, 1)) / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))

If ntresc = 1 Then
fas(bv1.Value, 3) = 1
fas(bv1.Value, 4) = tf - fas(bv1.Value, 1) + rs
End If
If ntresc > 1 Then
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(i, 3) = 1
fas(i, 4) = tf - fas(bv1.Value, 1) + rs
End If
Next
End If

Select Case ien
Case Is = 0
ie = "I"
Case Is = 1
ie = "E"
Case Is = 2
ie = " "
End Select
Select Case ud
Case Is = 0
udf = "U"
Case Is = 1
udf = "D"
Case Is = 2
udf = "+"
Case Is = 3
udf = "-"
Case Is = 4
udf = " "
End Select
Select Case pes
Case Is = 0
pe = "0"
Case Is = 1
pe = "1"
Case Is = 2
pe = "2"
Case Is = 3
pe = "3"
Case Is = 4
pe = "4"
End Select
Label15.Caption = Format(fas(bv1.Value, 4), "00.00") + ie + "S" + udf + pe
If ntresc = 1 Then
fas(bv1.Value, 5) = Format(fas(bv1.Value, 4), "00.00") + ie + "S" + udf + pe
End If
If ntresc > 1 Then
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(i, 5) = Format(fas(bv1.Value, 4), "00.00") + ie + "S" + udf + pe
End If
Next
End If

Else
MsgBox "Primero debe marcar la fase P!", 16, "Alto"
End If

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5

End Sub

Private Sub Command6_Click()
Dim rpha As String

If fas(bv1.Value, 0) = 1 Then
If ntresc = 1 Then
fas(bv1.Value, 6) = 1
fas(bv1.Value, 7) = Format((tf - fas(bv1.Value, 1)), "00.0")
Label15.Caption = Format((tf - fas(bv1.Value, 1)), "00.0")
End If
If ntresc > 1 Then
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(i, 6) = 1
fas(i, 7) = Format((tf - fas(bv1.Value, 1)), "00.0")
Label15.Caption = Format((tf - fas(bv1.Value, 1)), "00.0")
End If
Next
End If
Else
MsgBox "Primero debe marcar la fase P !", 16, "alto"
End If

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5

End Sub

Private Sub Command7_Click()
Dim rpha As String

Open "c:\Iaspei\FastHypo\fase.pha" For Output As #3
For i = 0 To 15
If fas(i, 0) = 1 And cab(i + 1, 0) = (15 - i) Then
Print #3, fas(i, 2); "       "; fas(i, 5); "                               "; fas(i, 7)
End If
Next
Print #3, "                 "; 10
Close #3

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5


Load Iaspei
Iaspei.Show 0

Iaspei.Label4.Caption = "fase.pha"

'fgr = Shell("c:\dia\hipof\convert1.pif", 1)
'hji = Shell("c:\dia\hipof\fast.pif", 2)

End Sub

Private Sub Command8_Click()
Dim rpha As String

If ntresc = 1 Then
fas(bv1.Value, 0) = 0
fas(bv1.Value, 1) = 0
fas(bv1.Value, 2) = "                        "
End If

If ntresc > 1 Then
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(i, 0) = 0
fas(i, 1) = 0
fas(i, 2) = "                        "
End If
Next
End If

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5

End Sub

Private Sub Command9_Click()
Dim rpha As String

If ntresc = 1 Then
fas(bv1.Value, 3) = 0
fas(bv1.Value, 4) = 0
fas(bv1.Value, 5) = "         "
End If
If ntresc > 1 Then
For i = 0 To 15
If cab(i + 1, 0) = cab(bv1.Value + 1, 0) Then
fas(i, 3) = 0
fas(i, 4) = 0
fas(i, 5) = "         "
End If
Next
End If

rpha = Mid(a.filename, 1, Len(a.filename) - 3) + "fas"
Open rpha For Binary Access Read Write As #5
For i = 0 To 15
For j = 0 To 7
Put #5, , fas(i, j)
Next
Next
Close #5

End Sub

Private Sub CWGraph1_CursorChange(CursorIndex As Long, XPos As Variant, YPos As Variant, bTracking As Boolean)
If CursorIndex = 1 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label1.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label2.Caption = "Y1:" + Format(YPos, "#.00")
px1 = XPos
End If
If CursorIndex = 2 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label3.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label4.Caption = "Y2:" + Format(YPos, "#.00")
px2 = XPos
End If

End Sub


Private Sub CWGraph1_MouseUp(Button As Integer, Shift As Integer, X As Single, Y As Single)
If Button = 1 Then
CWGraph1.TrackMode = 2
End If
If Button = 2 Then
CWGraph1.TrackMode = 6
End If
End Sub


Private Sub CWGraph2_CursorChange(CursorIndex As Long, XPos As Variant, YPos As Variant, bTracking As Boolean)
t1 = tiempo + px1 / 64 + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label11.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
tf = t1

If XPos < (px2 - px1) Then
If z(XPos + 1) - z(XPos) >= 0 Then
Label12.Caption = "Up"
ud = 0
Else
Label12.Caption = "Down"
ud = 1
End If
End If

End Sub


Private Sub CWGraph2_MouseUp(Button As Integer, Shift As Integer, X As Single, Y As Single)
If Button = 1 Then
CWGraph2.TrackMode = 2
End If
If Button = 2 Then
CWGraph2.TrackMode = 6
End If
End Sub


Private Sub CWGraph3_Click(Index As Integer)
If ntresc = 2 And Index = 2 Then
Label28.Caption = ""
itresc = 4
Else
Label28.Caption = est(ptresc(Index))
itresc = Index
End If

End Sub

Private Sub CWGraph3_CursorChange(Index As Integer, CursorIndex As Long, XPos As Variant, YPos As Variant, bTracking As Boolean)

If Index = 0 Then
If CursorIndex = 1 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label1.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label2.Caption = "Y1:" + Format(YPos, "#.00")
px1 = XPos
CWGraph3(1).Cursors.Item(1).PointIndex = CWGraph3(0).Cursors.Item(1).PointIndex
If ntresc = 3 Then
CWGraph3(2).Cursors.Item(1).PointIndex = CWGraph3(0).Cursors.Item(1).PointIndex
End If
End If
If CursorIndex = 2 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label3.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label4.Caption = "Y2:" + Format(YPos, "#.00")
px2 = XPos
CWGraph3(1).Cursors.Item(2).PointIndex = CWGraph3(0).Cursors.Item(2).PointIndex
If ntresc = 3 Then
CWGraph3(2).Cursors.Item(2).PointIndex = CWGraph3(0).Cursors.Item(2).PointIndex
End If

End If
End If

If Index = 1 Then
If CursorIndex = 1 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label1.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label2.Caption = "Y1:" + Format(YPos, "#.00")
px1 = XPos
CWGraph3(0).Cursors.Item(1).PointIndex = CWGraph3(1).Cursors.Item(1).PointIndex
If ntresc = 3 Then
CWGraph3(2).Cursors.Item(1).PointIndex = CWGraph3(1).Cursors.Item(1).PointIndex
End If
End If
If CursorIndex = 2 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label3.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label4.Caption = "Y2:" + Format(YPos, "#.00")
px2 = XPos
CWGraph3(0).Cursors.Item(2).PointIndex = CWGraph3(1).Cursors.Item(2).PointIndex
If ntresc = 3 Then
CWGraph3(2).Cursors.Item(2).PointIndex = CWGraph3(1).Cursors.Item(2).PointIndex
End If
End If
End If

If Index = 2 And ntresc = 3 Then
If CursorIndex = 1 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label1.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label2.Caption = "Y1:" + Format(YPos, "#.00")
px1 = XPos
CWGraph3(0).Cursors.Item(1).PointIndex = CWGraph3(2).Cursors.Item(1).PointIndex
CWGraph3(1).Cursors.Item(1).PointIndex = CWGraph3(2).Cursors.Item(1).PointIndex
End If
If CursorIndex = 2 Then
t1 = tiempo + XPos / 64
rh = t1 / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
Label3.Caption = Format(Int(rh), "00") + ":" + Format(Int(rm), "00") + ":" + Format(rs, "00.00")
Label4.Caption = "Y2:" + Format(YPos, "#.00")
px2 = XPos
CWGraph3(0).Cursors.Item(2).PointIndex = CWGraph3(2).Cursors.Item(2).PointIndex
CWGraph3(1).Cursors.Item(2).PointIndex = CWGraph3(2).Cursors.Item(2).PointIndex
End If
End If


End Sub


Private Sub CWGraph3_MouseUp(Index As Integer, Button As Integer, Shift As Integer, X As Single, Y As Single)
If Button = 1 Then
CWGraph3(Index).TrackMode = 2
End If
If Button = 2 Then
CWGraph3(Index).TrackMode = 6
End If

End Sub


Private Sub da_Click()
da.Enabled = False
Dim a As Double
Dim b As Double
ReDim s(ll * 64 - 1) As Double
a = 10 / 32768
b = 0
status = LinEvArray(X, a, b, s)
ru = "c:\dia\" + qw + est(bv1.Value) + ".dat"
Open ru For Output As #9
Print #9, qw
Print #9, est(bv1.Value)
For i = 0 To (ll * 64 - 1)
Print #9, s(i)
Next
Close #9
End Sub

Private Sub dac_Click()
das = InputBox("Ubicación de sismo?:", "Ingrese la localización:", "Lat.:00.00°S Long.:00.00°W Prof.:000Km. Mag.:0.0Md.")
End Sub

Private Sub Form_Load()
fs = 64
bv1.Value = 0
fl = 1
fh = 10
order = 1

For w = 0 To 15
fas(w, 2) = "                        "
fas(w, 5) = "         "
fas(w, 7) = "    "
Next

Command1.Enabled = False
Command2.Enabled = False
Command3.Enabled = False
Command11.Enabled = False
CWGraph3(0).Visible = False
CWGraph3(1).Visible = False
CWGraph3(2).Visible = False
CWGraph1.Visible = True
Label28.Visible = False
Command12.Enabled = False
Command13.Enabled = False
Command14.Enabled = False


Command4.Enabled = False
Command5.Enabled = False
command6.Enabled = False
Command7.Enabled = False
Command8.Enabled = False
Command9.Enabled = False
Command10.Enabled = False

End Sub




Private Sub gra_Click()
gra.Enabled = False
ru = "c:\dia\" + est(bv1.Value) + ".bln"
Open ru For Output As #4
Print #4, (ll * 64) / 4
For i = 0 To (ll * 64 - 1) Step 4
k(i) = i / 64
Print #4, Format(k(i), "#.000"), Format(Y(i), "#.000")
Next
Close #4
End Sub

Private Sub ims_Click()
For i = 0 To 15
cheche(i) = Check1(i).Value
Next

alista.filename = ""
alista.Action = 1

If alista.filename <> "" Then
Open alista.filename For Input As #7
iu = 0
Do While Not EOF(7)
Input #7, li(iu, 0)
Input #7, li(iu, 1)
iu = iu + 1
Loop
Close #7
conli = iu - 1
''abrir impresora
On Error GoTo rutinae
p.Action = 5

''abrir cada archivo
For iu = 0 To conli
For i = 0 To 15
Check1(i).Value = 0
Next
qwx = li(iu, 0)
Open qwx For Binary Access Read As #8
Get #8, , mmm
Get #8, , ccc
Get #8, , ttt
Get #8, , vvv
Get #8, , fec
ReDim cab(ccc, 8) As Variant
ReDim cabe(ccc, 8) As Variant

For i = 0 To ccc
For j = 0 To 8
Get #8, , cab(i, j)
cabe(i, j) = cab(i, j)
Next
Next
fca = Seek(8)

For i = 0 To 15
est(i) = cab(i + 1, 2)
Next

Label14.Caption = qwx

For i = 0 To 15
Check1(i).Value = cab(i + 1, 1)
Next
''imprimir cada archivo
Printer.FontName = "courier"
Printer.FontBold = False
Printer.FontSize = 6
Printer.Scale (0, 0)-(21, 29.7)
Printer.FontName = "Arial"
Printer.FontBold = True
Printer.FontSize = 5

ing = 7
cnp = 0
cnpi = 0
das = li(iu, 1)

''para chanlud

''Check1(0).Value = 1
''Check1(1).Value = 1

''Check1(5).Value = 0
''Check1(6).Value = 0
''para todos
If Check2.Value = 1 Then
For i = 0 To 15
Check1(i) = cheche(i)
Next
End If

For sv = 0 To 15
If Check1(sv).Value = 1 Then
cnpi = cnpi + 1
End If
Next

For sv = 0 To 15
If Check1(sv).Value = 1 Then
Get #8, , tiempo
rh = tiempo / 3600
rm = 60 * (rh - Int(rh))
rs = 60 * (rm - Int(rm))
l = FileLen(qwx)
l = (l - 8 - fca) / 2068
ll = l
ReDim X(l * 64 - 1) As Double
ReDim k(l * 64 - 1) As Double
i = 0
For t = 0 To l - 1
Get #8, , datos
For j = 0 To 63
X(i) = datos(sv, j)
i = i + 1
Next
Next

status = MaxMin1D(X, ma, ima, mi, imi)
Seek #8, fca
nd = l * 64
Call imprimir(X, ma, mi, ing, nd, est(sv))
ing = ing + 4.5
cnp = cnp + 1
End If

If cnp = 5 And cnp < cnpi Then
Call rotulo
cnp = 0
Printer.NewPage
ing = 7
End If

Next
Close #8

Call rotulo

''correcciones manuales
''Printer.Line (14, 4.3)-(14, 4.3)
''Printer.Print "INSTALADA EN PRUEBA                     "

''Printer.Line (14, 4.6)-(14, 4.6)
''Printer.Print "INSTALADA EN PRUEBA                     "


Printer.EndDoc
wwww = DoEvents()

Next

salir:
Exit Sub

rutinae:
Resume salir


End If
End Sub

Private Sub inf_Click()
Form2.Enabled = True
Form2.Show
Form2.Label6.Caption = mmm
Form2.Label7.Caption = ccc
Form2.Label8.Caption = ttt
Form2.Label9.Caption = vvv
Form2.Label10.Caption = fec
For i = 0 To 8
Form2.Label11(i) = cab(0, i)
Next

For i = 0 To 8
Form2.Label12(i) = cab(1, i)
Next

Form2.bh1.Max = ccc
Form2.bh1.Min = 1

End Sub

Private Sub Label17_Click()
Label17.ForeColor = QBColor(12)
Label18.ForeColor = QBColor(10)
Label19.ForeColor = QBColor(10)
Label20.ForeColor = QBColor(10)
Label21.ForeColor = QBColor(10)
pes = 0
End Sub

Private Sub Label18_Click()
Label17.ForeColor = QBColor(10)
Label18.ForeColor = QBColor(12)
Label19.ForeColor = QBColor(10)
Label20.ForeColor = QBColor(10)
Label21.ForeColor = QBColor(10)
pes = 1
End Sub


Private Sub Label19_Click()
Label17.ForeColor = QBColor(10)
Label18.ForeColor = QBColor(10)
Label19.ForeColor = QBColor(12)
Label20.ForeColor = QBColor(10)
Label21.ForeColor = QBColor(10)
pes = 2
End Sub


Private Sub Label20_Click()
Label17.ForeColor = QBColor(10)
Label18.ForeColor = QBColor(10)
Label19.ForeColor = QBColor(10)
Label20.ForeColor = QBColor(12)
Label21.ForeColor = QBColor(10)
pes = 3

End Sub


Private Sub Label21_Click()
Label17.ForeColor = QBColor(10)
Label18.ForeColor = QBColor(10)
Label19.ForeColor = QBColor(10)
Label20.ForeColor = QBColor(10)
Label21.ForeColor = QBColor(12)
pes = 4
End Sub


Private Sub Label22_Click()
Label22.ForeColor = QBColor(12)
Label23.ForeColor = QBColor(10)
Label24.ForeColor = QBColor(10)
ien = 0
End Sub


Private Sub Label23_Click()
Label22.ForeColor = QBColor(10)
Label23.ForeColor = QBColor(12)
Label24.ForeColor = QBColor(10)
ien = 1
End Sub


Private Sub Label24_Click()
Label22.ForeColor = QBColor(10)
Label23.ForeColor = QBColor(10)
Label24.ForeColor = QBColor(12)
ien = 2
End Sub


Private Sub Label25_Click()
Label25.ForeColor = QBColor(12)
Label26.ForeColor = QBColor(10)
Label27.ForeColor = QBColor(10)
ud = 2

End Sub


Private Sub Label26_Click()
Label25.ForeColor = QBColor(10)
Label26.ForeColor = QBColor(12)
Label27.ForeColor = QBColor(10)
ud = 3
End Sub


Private Sub Label27_Click()
Label25.ForeColor = QBColor(10)
Label26.ForeColor = QBColor(10)
Label27.ForeColor = QBColor(12)
ud = 4

End Sub




Private Sub salir_Click()
Close
End
End Sub


