VERSION 5.00
Begin VB.Form Form3 
   BackColor       =   &H00E0E0E0&
   Caption         =   "Ubicación del Sismo"
   ClientHeight    =   3015
   ClientLeft      =   4095
   ClientTop       =   435
   ClientWidth     =   3795
   LinkTopic       =   "Form3"
   ScaleHeight     =   3015
   ScaleWidth      =   3795
   Begin VB.CommandButton Command1 
      Caption         =   "Aceptar"
      Height          =   375
      Left            =   1200
      TabIndex        =   0
      Top             =   2400
      Width           =   1335
   End
End
Attribute VB_Name = "Form3"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub Command1_Click()
Form3.Visible = False
End Sub
