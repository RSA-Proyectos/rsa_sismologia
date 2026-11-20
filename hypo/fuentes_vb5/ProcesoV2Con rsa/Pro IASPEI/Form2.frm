VERSION 5.00
Begin VB.Form Form2 
   BackColor       =   &H00E0E0E0&
   Caption         =   "Ubicación del Sismo"
   ClientHeight    =   3015
   ClientLeft      =   4095
   ClientTop       =   435
   ClientWidth     =   3795
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   3015
   ScaleWidth      =   3795
   Begin VB.CommandButton Command1 
      BackColor       =   &H80000013&
      Caption         =   "Aceptar"
      Height          =   375
      Left            =   1200
      MaskColor       =   &H00E0E0E0&
      Style           =   1  'Graphical
      TabIndex        =   0
      Top             =   2400
      Width           =   1455
   End
End
Attribute VB_Name = "Form2"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub Command1_Click()
Form2.Visible = False
End Sub
