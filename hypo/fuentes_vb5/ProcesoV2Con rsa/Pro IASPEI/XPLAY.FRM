VERSION 5.00
Object = "{BDC217C8-ED16-11CD-956C-0000C04E4C0A}#1.1#0"; "TABCTL32.OCX"
Begin VB.Form Form1 
   Caption         =   "Proceso PCSUDS"
   ClientHeight    =   7425
   ClientLeft      =   60
   ClientTop       =   345
   ClientWidth     =   9255
   LinkTopic       =   "Form2"
   ScaleHeight     =   7425
   ScaleWidth      =   9255
   StartUpPosition =   1  'CenterOwner
   Begin VB.CommandButton Command1 
      Caption         =   "&Salir"
      BeginProperty Font 
         Name            =   "Arial"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   375
      TabIndex        =   6
      Top             =   6900
      Width           =   1215
   End
   Begin TabDlg.SSTab SSTab1 
      Height          =   6675
      Left            =   150
      TabIndex        =   0
      Top             =   150
      Width           =   8970
      _ExtentX        =   15822
      _ExtentY        =   11774
      _Version        =   393216
      Tabs            =   2
      Tab             =   1
      TabsPerRow      =   2
      TabHeight       =   520
      TabCaption(0)   =   "&XPLAY"
      TabPicture(0)   =   "XPLAY.frx":0000
      Tab(0).ControlEnabled=   0   'False
      Tab(0).Control(0)=   "Command3"
      Tab(0).Control(1)=   "Command2"
      Tab(0).Control(2)=   "Dir1"
      Tab(0).Control(3)=   "Drive1"
      Tab(0).Control(4)=   "File1"
      Tab(0).ControlCount=   5
      TabCaption(1)   =   "&Colocación de Fases y Proceso"
      TabPicture(1)   =   "XPLAY.frx":001C
      Tab(1).ControlEnabled=   -1  'True
      Tab(1).Control(0)=   "Drive2"
      Tab(1).Control(0).Enabled=   0   'False
      Tab(1).Control(1)=   "Dir2"
      Tab(1).Control(1).Enabled=   0   'False
      Tab(1).Control(2)=   "Frame1"
      Tab(1).Control(2).Enabled=   0   'False
      Tab(1).Control(3)=   "Frame2"
      Tab(1).Control(3).Enabled=   0   'False
      Tab(1).Control(4)=   "Frame3"
      Tab(1).Control(4).Enabled=   0   'False
      Tab(1).ControlCount=   5
      Begin VB.Frame Frame3 
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
         ForeColor       =   &H00000080&
         Height          =   3555
         Left            =   150
         TabIndex        =   18
         Top             =   3000
         Width           =   8655
         Begin VB.CommandButton Command16 
            Caption         =   "Borrar Archivo"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   345
            Left            =   4725
            TabIndex        =   51
            Top             =   3000
            Width           =   3735
         End
         Begin VB.CommandButton Command15 
            Caption         =   "&Renombrar"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   270
            Left            =   150
            TabIndex        =   50
            Top             =   2400
            Width           =   1440
         End
         Begin VB.CommandButton Command14 
            Caption         =   "&Refresh"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   270
            Left            =   150
            TabIndex        =   49
            Top             =   2100
            Width           =   1440
         End
         Begin VB.CommandButton Command13 
            Caption         =   "Editar Archivo"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   495
            Left            =   7275
            TabIndex        =   48
            Top             =   2400
            Width           =   1185
         End
         Begin VB.CommandButton Command12 
            Caption         =   "Editar Archivo"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   495
            Left            =   6000
            TabIndex        =   47
            Top             =   2400
            Width           =   1185
         End
         Begin VB.CommandButton Command11 
            Caption         =   "Editar Archivo"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   495
            Left            =   4725
            TabIndex        =   45
            Top             =   2400
            Width           =   1185
         End
         Begin VB.FileListBox File5 
            Height          =   1650
            Left            =   4725
            Pattern         =   "*.??p"
            TabIndex        =   44
            Top             =   600
            Width           =   1185
         End
         Begin VB.TextBox Text5 
            Height          =   285
            Left            =   1875
            TabIndex        =   38
            Text            =   "100"
            Top             =   3000
            Width           =   1440
         End
         Begin VB.CommandButton Command10 
            Caption         =   "Fpo&ng"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   345
            Left            =   3450
            TabIndex        =   37
            Top             =   1155
            Width           =   990
         End
         Begin VB.CommandButton Command9 
            Caption         =   "&Fast"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   345
            Left            =   3450
            TabIndex        =   36
            Top             =   525
            Width           =   990
         End
         Begin VB.TextBox Text4 
            Height          =   285
            Left            =   2550
            TabIndex        =   34
            Text            =   "60.0"
            Top             =   2370
            Width           =   765
         End
         Begin VB.TextBox Text3 
            Height          =   285
            Left            =   2550
            TabIndex        =   32
            Text            =   "-79.0"
            Top             =   2025
            Width           =   765
         End
         Begin VB.TextBox Text2 
            Height          =   285
            Left            =   2550
            TabIndex        =   30
            Text            =   "-2.5"
            Top             =   1680
            Width           =   765
         End
         Begin VB.TextBox Text1 
            Height          =   285
            Left            =   1875
            TabIndex        =   28
            Text            =   "asw"
            Top             =   1050
            Width           =   1440
         End
         Begin VB.FileListBox File7 
            Height          =   1650
            Left            =   7275
            Pattern         =   "*.??s"
            TabIndex        =   24
            Top             =   600
            Width           =   1185
         End
         Begin VB.FileListBox File6 
            Height          =   1650
            Left            =   6000
            Pattern         =   "*.??l"
            TabIndex        =   23
            Top             =   600
            Width           =   1185
         End
         Begin VB.FileListBox File4 
            Height          =   1455
            Left            =   135
            Pattern         =   "phase*.*"
            TabIndex        =   21
            Top             =   525
            Width           =   1500
         End
         Begin VB.CommandButton Command8 
            Caption         =   "B&orrar Archivo"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   270
            Left            =   150
            TabIndex        =   20
            Top             =   3000
            Width           =   1440
         End
         Begin VB.CommandButton Command7 
            Caption         =   "&Editar Archivo"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   270
            Left            =   150
            TabIndex        =   19
            Top             =   2700
            Width           =   1440
         End
         Begin VB.CheckBox Check1 
            Caption         =   "Ejecutar Convert"
            Height          =   390
            Left            =   3525
            TabIndex        =   40
            Top             =   2175
            Value           =   1  'Checked
            Width           =   915
         End
         Begin VB.CheckBox Check2 
            Caption         =   "Ejecutar Fast"
            Height          =   390
            Left            =   3525
            TabIndex        =   41
            Top             =   2700
            Value           =   1  'Checked
            Width           =   915
         End
         Begin VB.Label Label11 
            Caption         =   "Fases:"
            Height          =   240
            Left            =   4800
            TabIndex        =   46
            Top             =   375
            Width           =   765
         End
         Begin VB.Shape Shape4 
            BorderColor     =   &H80000003&
            Height          =   3165
            Left            =   4650
            Top             =   225
            Width           =   3915
         End
         Begin VB.Label Label13 
            Caption         =   "Solución:"
            Height          =   240
            Left            =   7275
            TabIndex        =   43
            Top             =   375
            Width           =   765
         End
         Begin VB.Label Label12 
            Caption         =   "Lista:"
            Height          =   240
            Left            =   6000
            TabIndex        =   42
            Top             =   375
            Width           =   765
         End
         Begin VB.Shape Shape3 
            BorderColor     =   &H80000003&
            Height          =   1140
            Left            =   3450
            Top             =   2100
            Width           =   1065
         End
         Begin VB.Label Label10 
            Caption         =   "Núm. de iteraciones:"
            Height          =   240
            Left            =   1875
            TabIndex        =   39
            Top             =   2775
            Width           =   1515
         End
         Begin VB.Shape Shape2 
            BorderColor     =   &H80000003&
            Height          =   3165
            Left            =   1800
            Top             =   225
            Width           =   2790
         End
         Begin VB.Label Label9 
            Caption         =   "Prof:"
            Height          =   240
            Left            =   2175
            TabIndex        =   35
            Top             =   2415
            Width           =   315
         End
         Begin VB.Label Label8 
            Caption         =   "Lon:"
            Height          =   240
            Left            =   2175
            TabIndex        =   33
            Top             =   2070
            Width           =   315
         End
         Begin VB.Label Label7 
            Caption         =   "Lat:"
            Height          =   240
            Left            =   2175
            TabIndex        =   31
            Top             =   1725
            Width           =   315
         End
         Begin VB.Shape Shape1 
            BorderColor     =   &H80000003&
            FillColor       =   &H80000003&
            Height          =   3165
            Left            =   75
            Top             =   225
            Width           =   1665
         End
         Begin VB.Label Label6 
            Caption         =   "Trial Values:"
            Height          =   240
            Left            =   1875
            TabIndex        =   29
            Top             =   1425
            Width           =   1290
         End
         Begin VB.Label Label5 
            Caption         =   "Modelo de corteza:"
            Height          =   240
            Left            =   1875
            TabIndex        =   27
            Top             =   825
            Width           =   1365
         End
         Begin VB.Label Label4 
            Alignment       =   2  'Center
            BorderStyle     =   1  'Fixed Single
            Height          =   240
            Left            =   1875
            TabIndex        =   26
            Top             =   525
            Width           =   1440
         End
         Begin VB.Label Label3 
            Caption         =   "Archivo:"
            Height          =   240
            Left            =   1875
            TabIndex        =   25
            Top             =   300
            Width           =   840
         End
         Begin VB.Label Label2 
            Caption         =   "Fases:"
            Height          =   240
            Left            =   150
            TabIndex        =   22
            Top             =   300
            Width           =   840
         End
      End
      Begin VB.Frame Frame2 
         Caption         =   "SUDS Pick"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00000080&
         Height          =   2535
         Left            =   5670
         TabIndex        =   14
         Top             =   480
         Width           =   3075
         Begin VB.CommandButton Command6 
            Caption         =   "&Crear Archivo de Fases"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   690
            Left            =   1785
            TabIndex        =   17
            Top             =   1500
            Width           =   1140
         End
         Begin VB.CommandButton Command5 
            Caption         =   "&Poner Fases"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   495
            Left            =   1800
            TabIndex        =   16
            Top             =   600
            Width           =   1140
         End
         Begin VB.FileListBox File3 
            Height          =   2040
            Left            =   105
            Pattern         =   "*.dmx"
            TabIndex        =   15
            Top             =   375
            Width           =   1575
         End
      End
      Begin VB.Frame Frame1 
         Caption         =   "Demux/Irig"
         BeginProperty Font 
            Name            =   "MS Sans Serif"
            Size            =   8.25
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00000080&
         Height          =   2535
         Left            =   2400
         TabIndex        =   9
         Top             =   480
         Width           =   3120
         Begin VB.OptionButton Option2 
            Caption         =   "Todos los archivos"
            Height          =   615
            Left            =   1800
            TabIndex        =   13
            Top             =   1560
            Width           =   1215
         End
         Begin VB.OptionButton Option1 
            Caption         =   "Archivos selecionados"
            Height          =   375
            Left            =   1785
            TabIndex        =   12
            Top             =   1080
            Value           =   -1  'True
            Width           =   1230
         End
         Begin VB.FileListBox File2 
            Height          =   2040
            Left            =   150
            MultiSelect     =   2  'Extended
            Pattern         =   "*.wvs"
            TabIndex        =   11
            Top             =   360
            Width           =   1575
         End
         Begin VB.CommandButton Command4 
            Caption         =   "&Demux/Irig"
            BeginProperty Font 
               Name            =   "MS Sans Serif"
               Size            =   8.25
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   495
            Left            =   1800
            TabIndex        =   10
            Top             =   375
            Width           =   1215
         End
      End
      Begin VB.DirListBox Dir2 
         Height          =   2115
         Left            =   120
         TabIndex        =   8
         Top             =   840
         Width           =   2145
      End
      Begin VB.DriveListBox Drive2 
         Height          =   315
         Left            =   120
         TabIndex        =   7
         Top             =   480
         Width           =   2145
      End
      Begin VB.FileListBox File1 
         Height          =   4575
         Left            =   -70365
         Pattern         =   "*.wvs"
         TabIndex        =   1
         Top             =   1800
         Width           =   3855
      End
      Begin VB.DriveListBox Drive1 
         Height          =   315
         Left            =   -74445
         TabIndex        =   5
         Top             =   1800
         Width           =   3735
      End
      Begin VB.DirListBox Dir1 
         Height          =   4140
         Left            =   -74445
         TabIndex        =   4
         Top             =   2160
         Width           =   3735
      End
      Begin VB.CommandButton Command2 
         Caption         =   "&Mostrar Evento"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   9.75
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   855
         Left            =   -74445
         TabIndex        =   2
         Top             =   720
         Width           =   3735
      End
      Begin VB.CommandButton Command3 
         Caption         =   "&Borrar Evento"
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   9.75
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   855
         Left            =   -70365
         TabIndex        =   3
         Top             =   750
         Width           =   3855
      End
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

Private Sub Command1_Click()
    End
End Sub

Private Sub Command10_Click()
Dim indicador As Long
Dim inicio, final, espera As Single
Dim www As Long
Dim FechaAntes, FechaDespues, Fecha As Variant
Dim i, num As Integer
Dim IndicadorFecha As Boolean
Dim Archivo As String



If Label4.Caption = "" And (Check1.Value = 1 Or Check2.Value = 1) Then
    MsgBox "Debe escoger un archivo de fases", 48, "Alerta"
    Exit Sub
ElseIf Check1.Value = 0 And Check2.Value = 0 Then
    Exit Sub
End If


If Check1.Value = 1 Then
    If Not (Left(Label4.Caption, 5) = "Phase" Or _
        Left(Label4.Caption, 5) = "phase" Or _
        Left(Label4.Caption, 5) = "PHASE") Then
          MsgBox "Debe escoger un archivo de fases 'Phase*.*'", 48, "Alerta"
          Exit Sub
    End If
ElseIf Check2.Value = 1 And Check1.Value = 0 Then
    If Not (Right(Label4.Caption, 1) = "P" Or _
        Left(Label4.Caption, 5) = "p") Then
          MsgBox "Debe escoger un archivo de fases '*.??P'", 48, "Alerta"
          Exit Sub
    End If
End If

If Check2.Value = True Then

    If Text1.Text = "" Then
        MsgBox "Debe ingresar un modelo de corteza", 48, "Alerta"
        Text1.SetFocus
        Exit Sub
    End If

    If IsNumeric(Text2.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Trial Value de Latitud", 48, "Alerta"
        Text2.Text = ""
        Text2.SetFocus
        Exit Sub
    End If

    If IsNumeric(Text3.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Trial Value de Longitud", 48, "Alerta"
        Text3.Text = ""
        Text3.SetFocus
        Exit Sub
    End If

    If IsNumeric(Text4.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Trial Value de Profundidad", 48, "Alerta"
        Text4.Text = ""
        Text4.SetFocus
        Exit Sub
    End If


    If IsNumeric(Text5.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Número de Iteraciones", 48, "Alerta"
        Text5.Text = ""
        Text5.SetFocus
        Exit Sub
    ElseIf Val(Text5.Text) <= 0 Then
        MsgBox "El Número de Iteraciones debe ser un número mayor que cero", 48, "Alerta"
        Text5.Text = ""
        Text5.SetFocus
        Exit Sub
    End If

End If



Archivo = ""

'----------------------------------------------
If Check1.Value = 1 Then 'Inicio

 IndicadorFecha = False

 If File5.ListCount > 0 Then
  FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(0))

  i = 1
  num = File5.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i)) >= _
        FechaAntes Then

        FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i))

    End If
  i = i + 1
  Loop
 Else
  IndicadorFecha = True
 End If


 Open "C:\IASPEI\FastHypo\convert.in" For Output As #1

 Print #1, Label4.Caption
 Print #1, "2"

 Close #1

 activa = GetActiveWindow()
 indicador = Shell("C:\Iaspei\FastHypo\conv1bat.bat", 3)
 inicio = Timer
 espera = 0.7

 Do While GetActiveWindow() = activa
    www = DoEvents()
    final = Timer
    If (final - inicio) > espera Then
        Exit Do
    End If
 Loop
                
 activa = GetActiveWindow()
 inicio = Timer
 Do While GetActiveWindow() = activa
    www = DoEvents()
    final = Timer
    If (final - inicio) > espera Then
        Exit Do
    End If
 Loop

 File5.Refresh
 File6.Refresh
 File7.Refresh

 File5.SetFocus


 If File5.ListCount > 0 Then
  
  FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(0))
  Archivo = File5.List(0)
  i = 1
  num = File5.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i)) >= _
        FechaDespues Then

        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i))
        Archivo = File5.List(i)
        
    End If
  i = i + 1
  
  Loop


  If IndicadorFecha = False Then
    If FechaDespues = FechaAntes Then
        MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & Label4.Caption, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Exit Sub
    End If
  End If
  
  
 Else
        MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & Label4.Caption, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
    Exit Sub
 End If

End If



'-------------------------------
If Check2.Value = 1 Then
    If Archivo = "" Then
        Archivo = Label4.Caption
    End If
    

 IndicadorFecha = False

 If File7.ListCount > 0 Then
  FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(0))

  i = 1
  num = File7.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
        FechaAntes Then

        FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i))

    End If
  i = i + 1
  Loop
 Else
  IndicadorFecha = True
 End If


 Open "C:\IASPEI\FastHypo\fpong.in" For Output As #1

 Print #1, Text1.Text
 Print #1, "y"
 Print #1, "r"
 Print #1, Archivo
 Print #1, "n"
 Print #1, Format(Text5.Text, "0")
 Print #1, Format(Text2.Text, "0.000") & "," & Format(Text3.Text, "0.000") _
           & "," & Format(Text4.Text, "0.000") & ",0"

 Close #1

 activa = GetActiveWindow()
 indicador = Shell("C:\Iaspei\FastHypo\fpongbat.bat", 3)
 inicio = Timer
 espera = 0.7

 Do While GetActiveWindow() = activa
    www = DoEvents()
    final = Timer
    If (final - inicio) > espera Then
        Exit Do
    End If
 Loop
                
                
 activa = GetActiveWindow()
 inicio = Timer
 Do While GetActiveWindow() = activa
    www = DoEvents()
 Loop
 
 'espera = 1
 'inicio = Timer
 'i = 1
 'Do While i = 1
 '   final = Timer
 '   If (final - inicio) > espera Then
 '       Exit Do
 '   End If
 'Loop




 File5.Refresh
 File6.Refresh
 File7.Refresh

 File5.SetFocus


If File7.ListCount > 0 Then
  
  FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(0))
  
  i = 1
  num = File7.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
        FechaDespues Then

        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i))
        
        
    End If
  i = i + 1
  
  Loop


  If IndicadorFecha = False Then
    If FechaDespues = FechaAntes Then
        MsgBox "El programa FPONG no se ejecutó adecuadamente" & Chr(13) & _
        "Revise los datos que introdujo o el contenido del archivo " & Archivo, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Exit Sub
    Else
    
        On Error GoTo ErrorArchivo
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(Archivo, Len(Archivo) - 1) & "L"
        File6.Refresh
        
        
        i = 1
        indicador = 0
        num = File6.ListCount
        Fecha = FileDateTime("C:\Iaspei\FastHypo\" & File6.List(0))
          Do While i < num
            If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
               Fecha Then

                indicador = i
        
            End If
          i = i + 1
  
          Loop
        
        File6.Selected(indicador) = True
        
    End If
  Else
    On Error GoTo ErrorArchivo
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(Archivo, Len(Archivo) - 1) & "L"
        File6.Refresh
        
        i = 1
        indicador = 0
        num = File6.ListCount
        Fecha = FileDateTime("C:\Iaspei\FastHypo\" & File6.List(0))
          Do While i < num
            If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
               Fecha Then

                indicador = i
        
            End If
          i = i + 1
  
          Loop
        
        File6.Selected(indicador) = True
  End If
  
  
Else
        MsgBox "El programa FPONG no se ejecutó adecuadamente" & Chr(13) & _
        "Revise los datos que introdujo o el contenido del archivo " & Archivo, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Exit Sub
End If


End If




MsgBox "Proceso Terminado", vbDefaultButton1, "CONVERT/FAST"
File4.Refresh
File5.Refresh
File6.Refresh
File7.Refresh

Exit Sub

ErrorArchivo:
    Kill ("C:\Iaspei\FastHypo\" & Left(Archivo, Len(Archivo) - 1) & "L")
    Resume

End Sub

Private Sub Command11_Click()
Dim indicador As Long
Dim Archivo As String

If File5.ListCount > 0 And File5.ListIndex >= 0 Then
    Archivo = File5.Path & "\" & File5.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & Archivo, 3)
End If
End Sub


Private Sub Command12_Click()
Dim indicador As Long
Dim Archivo As String

If File6.ListCount > 0 And File6.ListIndex >= 0 Then
    Archivo = File6.Path & "\" & File6.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & Archivo, 3)
End If
End Sub


Private Sub Command13_Click()
Dim indicador As Long
Dim Archivo As String

If File7.ListCount > 0 And File7.ListIndex >= 0 Then
    Archivo = File7.Path & "\" & File7.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & Archivo, 3)
End If

End Sub

Private Sub Command14_Click()
File4.Refresh
File5.Refresh
File6.Refresh
File7.Refresh
File4.SetFocus
End Sub

Private Sub Command15_Click()
Dim Archivo, Nuevo As String
Dim indice As Integer
If File4.ListCount > 0 And File4.ListIndex >= 0 Then
    indice = File4.ListIndex
    Archivo = File4.filename
    Nuevo = InputBox("Introduzca el nuevo nombre", "Renombrar Archivo de Fases", Archivo)
    
    If Nuevo = "" Or Nuevo = " " Then
        MsgBox "Debe ingresar un nombre adecuado para el archivo de fases", 48, "Alerta"
        Exit Sub
    End If
    
    Name (File4.Path & "\" & Archivo) As (File4.Path & "\" & Nuevo)
    File4.Refresh
    File4.Selected(indice) = True
    File4.SetFocus
    

End If
End Sub

Private Sub Command2_Click()
Dim Archivo As String
Dim RutaXplay As String
Dim indicador As Double

If File1.ListCount <> 0 Then
    Archivo = File1.Path & "\" & File1.filename
    RutaXplay = "C:\Iaspei\Pcsuds\Xplayv.exe"
    indicador = Shell(RutaXplay & " " & Archivo, 3)
End If

File1.Refresh

End Sub



Private Sub Command3_Click()
Dim indicador, indice As Integer

If File1.ListCount <> 0 And File1.ListIndex >= 0 Then

    indice = File1.ListIndex

    indicador = MsgBox("Está seguro que desea eliminar el archivo " _
    & File1.filename, vbYesNo, Alerta)
    

    
    If indicador = 6 Then
        On Error GoTo ErrorBorrar
        Kill Dir1.Path & "\" & File1.filename
        File1.Refresh
        File.Refresh
        File1.SetFocus
    
        If File1.ListCount <> 0 And indice <= File1.ListCount - 1 Then
            File1.Selected(indice) = True
        ElseIf File1.ListCount <> 0 Then
            File1.Selected(File1.ListCount - 1) = True
        End If
        
    Else
        On Error GoTo ErrorBorrar
        File1.Refresh
        File2.SetFocus
        File1.Selected(indice) = True
    End If
    
End If

Exit Sub

ErrorBorrar:
File1.Refresh
Exit Sub
    
End Sub

Private Sub Command4_Click()
Dim indice, www As Integer
Dim indicador As Double
Dim espera, inicio, final As Single
Dim activa, irg, dem As Long
Dim Archivo, RutaDemux, RutaIrig As String
    indice = 1
    espera = 0.7
    RutaDemux = "C:\Iaspei\Pcsuds\Demux.exe"
    RutaIrig = "C:\Iaspei\Pcsuds\Irig.exe"
    
    If Option1.Value = True And File2.ListIndex <> -1 Then
    
      Do While indice <= 10000
        If indice <= File2.ListCount Then
            
            If File2.Selected(indice - 1) = True Then
                
                Archivo = File1.Path & "\" & File2.List(indice - 1)
                activa = GetActiveWindow()
                
                'IRIG
                indicador = Shell(RutaIrig & " " & Archivo, 3)
                
                inicio = Timer
                Do While GetActiveWindow() = activa
                    www = DoEvents()
                    final = Timer
                    If (final - inicio) > espera Then
                        Exit Do
                    End If
                Loop
                
                irg = GetActiveWindow()
                
                inicio = Timer
                Do While GetActiveWindow() = irg
                www = DoEvents()
                final = Timer
                If (final - inicio) > espera Then
                    Exit Do
                End If
                Loop
                
                'DEMUX
                
                indicador = Shell(RutaDemux & " " & Archivo, 3)
                
                inicio = Timer
                Do While GetActiveWindow() = activa
                www = DoEvents()
                final = Timer
                If (final - inicio) > espera Then
                    Exit Do
                End If
                i = i + 1
                Loop
                
                dem = GetActiveWindow()
                inicio = Timer
                Do While GetActiveWindow() = dem
                www = DoEvents()
                final = Timer
                If (final - inicio) > espera Then
                    Exit Do
                End If
                Loop
                
                
                File3.Refresh
            End If
            
            indice = indice + 1
        Else
            Exit Do
        End If
      Loop
      MsgBox "Proceso terminado satisfactoriamente", vbOKOnly, "Demux/Irig"
    
    ElseIf Option2.Value = True Then
    RutaDemux = "C:\Iaspei\Pcsuds\Demux.exe"
    RutaIrig = "C:\Iaspei\Pcsuds\Irig.exe"

      Do While indice <= File2.ListCount
                    
        
                Archivo = File1.Path & "\" & File2.List(indice - 1)
                                
                activa = GetActiveWindow()
                
                'IRIG
                indicador = Shell(RutaIrig & " " & Archivo, 3)
                
                inicio = Timer
                Do While GetActiveWindow() = activa
                    www = DoEvents()
                    final = Timer
                    If (final - inicio) > espera Then
                        Exit Do
                    End If
                Loop
                
                irg = GetActiveWindow()
                
                inicio = Timer
                Do While GetActiveWindow() = irg
                www = DoEvents()
                final = Timer
                If (final - inicio) > espera Then
                    Exit Do
                End If
                Loop
                
                'DEMUX
                
                indicador = Shell(RutaDemux & " " & Archivo, 3)
                
                inicio = Timer
                Do While GetActiveWindow() = activa
                www = DoEvents()
                final = Timer
                If (final - inicio) > espera Then
                    Exit Do
                End If
                i = i + 1
                Loop
                
                dem = GetActiveWindow()
                inicio = Timer
                Do While GetActiveWindow() = dem
                www = DoEvents()
                final = Timer
                If (final - inicio) > espera Then
                    Exit Do
                End If
                Loop
                
                
                File3.Refresh
        
            
        indice = indice + 1
      Loop
      MsgBox "Proceso terminado satisfactoriamente", vbOKOnly, "Demux/Irig"

    End If
    File2.Refresh
    File2.SetFocus
    
End Sub


Private Sub Command5_Click()
Dim Archivo As String
Dim RutaSuds As String
Dim indicador As Double
Dim indice As Integer

If File3.ListCount <> 0 Then
    Archivo = File3.Path & "\" & File3.filename
    indice = File3.ListIndex
    RutaSuds = "C:\Iaspei\Pcsuds\Sudspick.exe"
    indicador = Shell(RutaSuds & " " & Archivo, 3)
End If
File2.Refresh
File3.Refresh
File3.Selected(indice) = True

End Sub


Private Sub Command6_Click()
Dim Archivo, ArchSal As String
Dim RutaXtrhy As String
Dim indicador As Double
Dim Salida As String
Dim activa As Long
Dim espera As Single
Dim IndicadorFecha As Boolean
Dim i, indice, num As Integer
Dim www As Integer

espera = 0.7
IndicadorFecha = False

If File3.ListCount <> 0 And File3.ListIndex >= 0 Then
    indice = File3.ListIndex
    File4.Refresh
    
    If File4.ListCount > 0 Then
        FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File4.List(0))
        i = 1
        num = File4.ListCount
        Do While i < num
            If FileDateTime("C:\Iaspei\FastHypo\" & File4.List(i)) >= _
            FechaAntes Then
                FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File4.List(i))
            End If
        i = i + 1
        Loop
    Else
    IndicadorFecha = True
    End If
    
    Salida = InputBox("Introduzca el nombre para el archivo de fases", "Archivo de fases")
    If Salida = "" Then
        Exit Sub
    End If
    
    ArchSal = Salida
    Salida = "C:\Iaspei\FastHypo" & "\" & Salida
    
    Archivo = File3.Path & "\" & File3.filename
    Arch = File3.filename
    
    RutaXtrhy = "C:\Iaspei\Pcsuds\Xtrhy71.exe"
    
    activa = GetActiveWindow()
                
    indicador = Shell(RutaXtrhy & " " & Archivo & " " & Salida, 3)
                
    inicio = Timer
        Do While GetActiveWindow() = activa
            www = DoEvents()
            final = Timer
            If (final - inicio) > espera Then
                Exit Do
            End If
        Loop
        
    activa = GetActiveWindow()
    inicio = Timer
        Do While GetActiveWindow() = activa
            www = DoEvents()
            final = Timer
            If (final - inicio) > espera Then
                Exit Do
            End If
        Loop
    
    
    File2.Refresh
    File3.Refresh
    File4.Refresh
    
    If File4.ListCount > 0 Then
        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File4.List(0))
        i = 1
        num = File4.ListCount
        Do While i < num
            If FileDateTime("C:\Iaspei\FastHypo\" & File4.List(i)) >= _
            FechaDespues Then
                FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File4.List(i))
            End If
        i = i + 1
        Loop
        
        If IndicadorFecha = False Then
            If FechaDespues = FechaAntes Then
                MsgBox "No fue posible crear el archivo '" & ArchSal _
                & "' que contiene las fases", 48, "Alerta"
                Exit Sub
            End If
        End If
    Else
        MsgBox "No fue posible crear el archivo '" & ArchSal _
                & "' que contiene las fases", 48, "Alerta"
        Exit Sub
    End If

    File3.Selected(indice) = True
    MsgBox "Proceso terminado satisfactoriamente", vbDefaultButton1, "FASES"
    
    
End If


End Sub

Private Sub Command7_Click()
Dim indicador As Long
Dim Archivo As String

If File4.ListCount > 0 And File4.ListIndex >= 0 Then
    Archivo = File4.Path & "\" & File4.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & Archivo, 3)
End If
End Sub

Private Sub Command8_Click()
Dim indicador As Single


If File4.ListCount > 0 And File4.ListIndex >= 0 Then

    indicador = MsgBox("¿Está seguro que desea borra el archivo " & _
                        File4.filename & "?", vbYesNo, "Alerta")
    If indicador = 6 Then
        Kill File4.Path & "\" & File4.filename
        File4.Refresh
    End If
    
End If

End Sub

Private Sub Command9_Click()
Dim indicador As Long
Dim inicio, final, espera As Single
Dim www As Long
Dim FechaAntes, FechaDespues, Fecha As Variant
Dim i, num As Integer
Dim IndicadorFecha As Boolean
Dim Archivo As String



If Label4.Caption = "" And (Check1.Value = 1 Or Check2.Value = 1) Then
    MsgBox "Debe escoger un archivo de fases", 48, "Alerta"
    Exit Sub
ElseIf Check1.Value = 0 And Check2.Value = 0 Then
    Exit Sub
End If


If Check1.Value = 1 Then
    If Not (Left(Label4.Caption, 5) = "Phase" Or _
        Left(Label4.Caption, 5) = "phase" Or _
        Left(Label4.Caption, 5) = "PHASE") Then
          MsgBox "Debe escoger un archivo de fases 'Phase*.*'", 48, "Alerta"
          Exit Sub
    End If
ElseIf Check2.Value = 1 And Check1.Value = 0 Then
    If Not (Right(Label4.Caption, 1) = "P" Or _
        Left(Label4.Caption, 5) = "p") Then
          MsgBox "Debe escoger un archivo de fases '*.??P'", 48, "Alerta"
          Exit Sub
    End If
End If

If Check2.Value = True Then

    If Text1.Text = "" Then
        MsgBox "Debe ingresar un modelo de corteza", 48, "Alerta"
        Text1.SetFocus
        Exit Sub
    End If

    If IsNumeric(Text2.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Trial Value de Latitud", 48, "Alerta"
        Text2.Text = ""
        Text2.SetFocus
        Exit Sub
    End If

    If IsNumeric(Text3.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Trial Value de Longitud", 48, "Alerta"
        Text3.Text = ""
        Text3.SetFocus
        Exit Sub
    End If

    If IsNumeric(Text4.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Trial Value de Profundidad", 48, "Alerta"
        Text4.Text = ""
        Text4.SetFocus
        Exit Sub
    End If


    If IsNumeric(Text5.Text) = False Then
        MsgBox "Debe introducir un valor numérico para el Número de Iteraciones", 48, "Alerta"
        Text5.Text = ""
        Text5.SetFocus
        Exit Sub
    ElseIf Val(Text5.Text) <= 0 Then
        MsgBox "El Número de Iteraciones debe ser un número mayor que cero", 48, "Alerta"
        Text5.Text = ""
        Text5.SetFocus
        Exit Sub
    End If

End If



Archivo = ""

'----------------------------------------------
If Check1.Value = 1 Then 'Inicio

 IndicadorFecha = False

 If File5.ListCount > 0 Then
  FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(0))

  i = 1
  num = File5.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i)) >= _
        FechaAntes Then

        FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i))

    End If
  i = i + 1
  Loop
 Else
  IndicadorFecha = True
 End If


 Open "C:\IASPEI\FastHypo\convert.in" For Output As #1

 Print #1, Label4.Caption
 Print #1, "2"

 Close #1

 activa = GetActiveWindow()
 indicador = Shell("C:\Iaspei\FastHypo\conv1bat.bat", 3)
 inicio = Timer
 espera = 0.7

 Do While GetActiveWindow() = activa
    www = DoEvents()
    final = Timer
    If (final - inicio) > espera Then
        Exit Do
    End If
 Loop
                
 activa = GetActiveWindow()
 inicio = Timer
 Do While GetActiveWindow() = activa
    www = DoEvents()
    final = Timer
    If (final - inicio) > espera Then
        Exit Do
    End If
 Loop

 File5.Refresh
 File6.Refresh
 File7.Refresh

 File5.SetFocus


 If File5.ListCount > 0 Then
  
  FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(0))
  Archivo = File5.List(0)
  i = 1
  num = File5.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i)) >= _
        FechaDespues Then

        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i))
        Archivo = File5.List(i)
        
    End If
  i = i + 1
  
  Loop


  If IndicadorFecha = False Then
    If FechaDespues = FechaAntes Then
        MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & Label4.Caption, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Exit Sub
    End If
  End If
  
  
 Else
        MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & Label4.Caption, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
    Exit Sub
 End If

End If



'-------------------------------
If Check2.Value = 1 Then
    If Archivo = "" Then
        Archivo = Label4.Caption
    End If
    

 IndicadorFecha = False

 If File7.ListCount > 0 Then
  FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(0))

  i = 1
  num = File7.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
        FechaAntes Then

        FechaAntes = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i))

    End If
  i = i + 1
  Loop
 Else
  IndicadorFecha = True
 End If


 Open "C:\IASPEI\FastHypo\fast.in" For Output As #1

 Print #1, Text1.Text
 Print #1, "y"
 Print #1, "r"
 Print #1, Archivo
 Print #1, "n"
 Print #1, Format(Text5.Text, "0")
 Print #1, Format(Text2.Text, "0.000") & "," & Format(Text3.Text, "0.000") _
           & "," & Format(Text4.Text, "0.000") & ",0"
 Print #1, "n"
 Print #1, "done"
 Close #1

 activa = GetActiveWindow()
 indicador = Shell("C:\Iaspei\FastHypo\fastbat.bat", 3)
 inicio = Timer
 espera = 0.7

 Do While GetActiveWindow() = activa
    www = DoEvents()
    final = Timer
    If (final - inicio) > espera Then
        Exit Do
    End If
 Loop
                
                
 activa = GetActiveWindow()
 inicio = Timer
 Do While GetActiveWindow() = activa
    www = DoEvents()
 Loop
 
 'espera = 1
 'inicio = Timer
 'i = 1
 'Do While i = 1
 '   final = Timer
 '   If (final - inicio) > espera Then
 '       Exit Do
 '   End If
 'Loop




 File5.Refresh
 File6.Refresh
 File7.Refresh

 File5.SetFocus


If File7.ListCount > 0 Then
  
  FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(0))
  
  i = 1
  num = File7.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
        FechaDespues Then

        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i))
        
        
    End If
  i = i + 1
  
  Loop


  If IndicadorFecha = False Then
    If FechaDespues = FechaAntes Then
        MsgBox "El programa FAST no se ejecutó adecuadamente" & Chr(13) & _
        "Revise los datos que introdujo o el contenido del archivo " & Archivo, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Exit Sub
    Else
    
        On Error GoTo ErrorArchivo
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(Archivo, Len(Archivo) - 1) & "L"
        File6.Refresh
        
        
        i = 1
        indicador = 0
        num = File6.ListCount
        Fecha = FileDateTime("C:\Iaspei\FastHypo\" & File6.List(0))
          Do While i < num
            If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
               Fecha Then

                indicador = i
        
            End If
          i = i + 1
  
          Loop
        
        File6.Selected(indicador) = True
        
    End If
  Else
    On Error GoTo ErrorArchivo
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(Archivo, Len(Archivo) - 1) & "L"
        File6.Refresh
        
        i = 1
        indicador = 0
        num = File6.ListCount
        Fecha = FileDateTime("C:\Iaspei\FastHypo\" & File6.List(0))
          Do While i < num
            If FileDateTime("C:\Iaspei\FastHypo\" & File7.List(i)) >= _
               Fecha Then

                indicador = i
        
            End If
          i = i + 1
  
          Loop
        
        File6.Selected(indicador) = True
  End If
  
  
Else
        MsgBox "El programa FAST no se ejecutó adecuadamente" & Chr(13) & _
        "Revise los datos que introdujo o el contenido del archivo " & Archivo, 48, "Alerta"
        File4.Refresh
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Exit Sub
End If


End If




MsgBox "Proceso Terminado", vbDefaultButton1, "CONVERT/FAST"
File4.Refresh
File5.Refresh
File6.Refresh
File7.Refresh

Exit Sub

ErrorArchivo:
    Kill ("C:\Iaspei\FastHypo\" & Left(Archivo, Len(Archivo) - 1) & "L")
    Resume
End Sub

Private Sub Dir1_Change()
File1.Path = Dir1.Path
End Sub

Private Sub Dir1_KeyDown(KeyCode As Integer, Shift As Integer)
continuar:
If KeyCode = 13 Then
    On Error GoTo ErrorDirectorio
    Dir1.Path = Dir1.List(Dir1.ListIndex)
End If

Exit Sub

ErrorDirectorio:
    Dir1.Refresh
    Resume continuar

End Sub

Private Sub Dir2_Change()
File2.Path = Dir2.Path
File3.Path = Dir2.Path
End Sub


Private Sub Drive1_Change()

On Error GoTo ErrorDisco
    Dir1.Path = Drive1.Drive
    Exit Sub

ErrorDisco:
    MsgBox "No se puede tener acceso al disco", 48, "Error de disco"
    Drive1.Drive = "C:"
    Dir1.Path = "C:\Iaspei\Registro"
End Sub


Private Sub Drive2_Change()
On Error GoTo ErrorDisco
    Dir2.Path = Drive2.Drive
    Exit Sub

ErrorDisco:
    MsgBox "No se puede tener acceso al disco", 48, "Error de disco"
    Drive2.Drive = "C:"
    Dir2.Path = "C:\Iaspei\Registro"

End Sub

Private Sub File1_DblClick()
Dim Archivo As String
Dim RutaXplay As String
Dim indicador As Double

    Archivo = File1.Path & "\" & File1.filename
    RutaXplay = "C:\Iaspei\Pcsuds\Xplayv.exe"
    indicador = Shell(RutaXplay & " " & Archivo, 3)

End Sub

Private Sub File1_KeyDown(KeyCode As Integer, Shift As Integer)
Dim Archivo As String
Dim RutaXplay As String
Dim indicador As Double

If KeyCode = 13 Then

    If File1.ListCount <> 0 Then
        Archivo = File1.Path & "\" & File1.filename
        RutaXplay = "C:\Iaspei\Pcsuds\Xplayv.exe"
        indicador = Shell(RutaXplay & " " & Archivo, 3)
    End If

End If

End Sub

Private Sub File1_MouseDown(Button As Integer, Shift As Integer, X As Single, Y As Single)
Dim indicador, indice As Integer

indice = File1.ListIndex

If Button = 2 Then
    If File1.ListCount <> 0 Then
        indicador = MsgBox("Está seguro que desea eliminar el archivo " _
        & File1.filename, vbYesNo, Alerta)
        
        If indicador = 6 Then
            On Error GoTo ErrorBorrar
            Kill Dir1.Path & "\" & File1.filename
            File1.Refresh
            File2.Refresh
            File1.SetFocus
            
            If File1.ListCount <> 0 And indice <= File1.ListCount - 1 Then
                File1.Selected(indice) = True
            ElseIf File1.ListCount <> 0 Then
                File1.Selected(File1.ListCount - 1) = True
            End If
            
        Else
            On Error GoTo ErrorBorrar
            File1.Refresh
            File1.SetFocus
            File1.Selected(indice) = True

            
        End If
    
    End If

End If
        
Exit Sub

ErrorBorrar:

File1.Refresh
Exit Sub
 
End Sub



Private Sub File4_Click()
If File4.ListCount > 0 Then
    Label4.Caption = File4.filename
Else
    Label4.Caption = ""
End If

End Sub

Private Sub File5_Click()
If File5.ListCount > 0 Then
    Label4.Caption = File5.filename
End If



End Sub



Private Sub Form_Activate()
File4.Refresh
End Sub


Private Sub Form_Load()
Dir1.Path = "C:\Iaspei\Registro"
Dir2.Path = "C:\Iaspei\Registro"
If File2.ListCount <> 0 Then
    File2.Selected(0) = True
End If
File4.Path = "C:\Iaspei\FastHypo"
File5.Path = "C:\Iaspei\FastHypo"
File6.Path = "C:\Iaspei\FastHypo"
File7.Path = "C:\Iaspei\FastHypo"
End Sub



Private Sub OLE2_Updated(Code As Integer)

End Sub

Private Sub OLE1_Updated(Code As Integer)

End Sub
