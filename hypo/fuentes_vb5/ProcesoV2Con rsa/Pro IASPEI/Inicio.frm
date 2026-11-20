VERSION 5.00
Begin VB.Form Incial 
   BorderStyle     =   3  'Fixed Dialog
   ClientHeight    =   4245
   ClientLeft      =   255
   ClientTop       =   1410
   ClientWidth     =   7380
   ClipControls    =   0   'False
   ControlBox      =   0   'False
   Icon            =   "Inicio.frx":0000
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form2"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   4245
   ScaleWidth      =   7380
   ShowInTaskbar   =   0   'False
   StartUpPosition =   2  'CenterScreen
   Begin VB.Frame Frame1 
      Height          =   4050
      Left            =   150
      TabIndex        =   0
      Top             =   75
      Width           =   7080
      Begin VB.Timer Timer1 
         Interval        =   3000
         Left            =   3750
         Top             =   2475
      End
      Begin VB.Label Label1 
         Caption         =   "Copyright 1999"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   8.25
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   4350
         TabIndex        =   8
         Top             =   3675
         Width           =   2415
      End
      Begin VB.Label lblDescription 
         Caption         =   "Programa para el procesamiento y localización de enventos sísmicos. Formato PC SUDS"
         ForeColor       =   &H00000000&
         Height          =   645
         Left            =   4245
         TabIndex        =   7
         Top             =   1500
         Width           =   2610
      End
      Begin VB.Image imgLogo 
         Height          =   2535
         Left            =   225
         Picture         =   "Inicio.frx":000C
         Stretch         =   -1  'True
         Top             =   1425
         Width           =   3240
      End
      Begin VB.Label lblCopyright 
         Caption         =   "Cuenca - Ecuador"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   8.25
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   4350
         TabIndex        =   2
         Top             =   3450
         Width           =   2415
      End
      Begin VB.Label lblCompany 
         Caption         =   "Ing. Gustavo Calle Vásquez"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   8.25
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   4350
         TabIndex        =   1
         Top             =   3195
         Width           =   2415
      End
      Begin VB.Label lblVersion 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         Caption         =   "Versión"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   12
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   285
         Left            =   5970
         TabIndex        =   3
         Top             =   2700
         Width           =   885
      End
      Begin VB.Label lblPlatform 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         Caption         =   "para Windows"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   15.75
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   360
         Left            =   4710
         TabIndex        =   4
         Top             =   2340
         Width           =   2145
      End
      Begin VB.Label lblProductName 
         AutoSize        =   -1  'True
         Caption         =   "PROCESO IASPEI"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   32.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   765
         Left            =   870
         TabIndex        =   6
         Top             =   690
         Width           =   5535
      End
      Begin VB.Label lblCompanyProduct 
         AutoSize        =   -1  'True
         Caption         =   "Red Sísmica del Austro"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   18
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   435
         Left            =   1620
         TabIndex        =   5
         Top             =   255
         Width           =   4020
      End
   End
End
Attribute VB_Name = "Incial"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

Option Explicit

Private Sub Form_KeyPress(KeyAscii As Integer)
    Unload Me
End Sub

Private Sub Form_Load()
    lblVersion.Caption = "Versión " & App.Major & "." & App.Minor & "." & App.Revision
    lblProductName.Caption = App.Title
End Sub

Private Sub Frame1_Click()
    Unload Me
End Sub

Private Sub Timer1_Timer()
    Timer1.Enabled = False
    Unload Me
    Load Iaspei
    Iaspei.Show
    
    
End Sub
