VERSION 5.00
Begin VB.Form Iaspei 
   Caption         =   "Proceso"
   ClientHeight    =   4245
   ClientLeft      =   60
   ClientTop       =   345
   ClientWidth     =   8865
   Icon            =   "Iaspei.frx":0000
   LinkTopic       =   "Form2"
   ScaleHeight     =   4245
   ScaleWidth      =   8865
   StartUpPosition =   1  'CenterOwner
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
      Left            =   75
      TabIndex        =   2
      Top             =   75
      Width           =   8655
      Begin VB.CheckBox Check2 
         Caption         =   "Ejecutar Fast"
         Height          =   390
         Left            =   3525
         TabIndex        =   22
         Top             =   2700
         Value           =   1  'Checked
         Width           =   915
      End
      Begin VB.CheckBox Check1 
         Caption         =   "Ejecutar Convert"
         Height          =   390
         Left            =   3525
         TabIndex        =   21
         Top             =   2175
         Value           =   1  'Checked
         Width           =   915
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
         TabIndex        =   20
         Top             =   2660
         Width           =   1440
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
         TabIndex        =   19
         Top             =   3000
         Width           =   1440
      End
      Begin VB.FileListBox File4 
         Height          =   1650
         Left            =   135
         Pattern         =   "phase*.*;fase.pha"
         TabIndex        =   18
         Top             =   525
         Width           =   1500
      End
      Begin VB.FileListBox File6 
         Height          =   1650
         Left            =   6000
         Pattern         =   "*.??l"
         TabIndex        =   17
         Top             =   600
         Width           =   1230
      End
      Begin VB.FileListBox File7 
         Height          =   1650
         Left            =   7275
         Pattern         =   "*.??s"
         TabIndex        =   16
         Top             =   600
         Width           =   1230
      End
      Begin VB.TextBox Text1 
         Height          =   285
         Left            =   1875
         TabIndex        =   15
         Text            =   "asw"
         Top             =   1050
         Width           =   1440
      End
      Begin VB.TextBox Text2 
         Height          =   285
         Left            =   2550
         TabIndex        =   14
         Text            =   "-2.5"
         Top             =   1680
         Width           =   765
      End
      Begin VB.TextBox Text3 
         Height          =   285
         Left            =   2550
         TabIndex        =   13
         Text            =   "-79.0"
         Top             =   2025
         Width           =   765
      End
      Begin VB.TextBox Text4 
         Height          =   285
         Left            =   2550
         TabIndex        =   12
         Text            =   "60.0"
         Top             =   2370
         Width           =   765
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
         Left            =   3480
         TabIndex        =   11
         Top             =   525
         Width           =   990
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
         Left            =   3480
         TabIndex        =   10
         Top             =   1155
         Width           =   990
      End
      Begin VB.TextBox Text5 
         Height          =   285
         Left            =   1875
         TabIndex        =   9
         Text            =   "100"
         Top             =   3000
         Width           =   1440
      End
      Begin VB.FileListBox File5 
         Height          =   1650
         Left            =   4725
         Pattern         =   "*.??p"
         TabIndex        =   8
         Top             =   600
         Width           =   1230
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
         TabIndex        =   7
         Top             =   2400
         Width           =   1230
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
         TabIndex        =   6
         Top             =   2400
         Width           =   1230
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
         TabIndex        =   5
         Top             =   2400
         Width           =   1230
      End
      Begin VB.CommandButton Command15 
         Caption         =   "Ren&ombrar"
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
         TabIndex        =   4
         Top             =   2320
         Width           =   1440
      End
      Begin VB.CommandButton Command16 
         Caption         =   "Borrar Archivos"
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
         TabIndex        =   3
         Top             =   3000
         Width           =   3735
      End
      Begin VB.Label Label4 
         Alignment       =   2  'Center
         BorderStyle     =   1  'Fixed Single
         Height          =   240
         Left            =   1875
         TabIndex        =   32
         Top             =   525
         Width           =   1440
      End
      Begin VB.Label Label2 
         Caption         =   "Fases:"
         Height          =   240
         Left            =   150
         TabIndex        =   34
         Top             =   300
         Width           =   840
      End
      Begin VB.Label Label3 
         Caption         =   "Archivo:"
         Height          =   240
         Left            =   1875
         TabIndex        =   33
         Top             =   300
         Width           =   840
      End
      Begin VB.Label Label5 
         Caption         =   "Modelo de corteza:"
         Height          =   240
         Left            =   1875
         TabIndex        =   31
         Top             =   825
         Width           =   1365
      End
      Begin VB.Label Label6 
         Caption         =   "Trial Values:"
         Height          =   240
         Left            =   1875
         TabIndex        =   30
         Top             =   1425
         Width           =   1290
      End
      Begin VB.Shape Shape1 
         BorderColor     =   &H80000003&
         FillColor       =   &H80000003&
         Height          =   3165
         Left            =   75
         Top             =   225
         Width           =   1665
      End
      Begin VB.Label Label7 
         Caption         =   "Lat:"
         Height          =   240
         Left            =   2175
         TabIndex        =   29
         Top             =   1725
         Width           =   315
      End
      Begin VB.Label Label8 
         Caption         =   "Lon:"
         Height          =   240
         Left            =   2175
         TabIndex        =   28
         Top             =   2070
         Width           =   315
      End
      Begin VB.Label Label9 
         Caption         =   "Prof:"
         Height          =   240
         Left            =   2175
         TabIndex        =   27
         Top             =   2415
         Width           =   315
      End
      Begin VB.Shape Shape2 
         BorderColor     =   &H80000003&
         Height          =   3165
         Left            =   1800
         Top             =   225
         Width           =   2790
      End
      Begin VB.Label Label10 
         Caption         =   "Núm. de iteraciones:"
         Height          =   240
         Left            =   1875
         TabIndex        =   26
         Top             =   2775
         Width           =   1515
      End
      Begin VB.Shape Shape3 
         BorderColor     =   &H80000003&
         Height          =   1140
         Left            =   3450
         Top             =   2100
         Width           =   1065
      End
      Begin VB.Label Label12 
         Caption         =   "Lista:"
         Height          =   240
         Left            =   6000
         TabIndex        =   25
         Top             =   375
         Width           =   765
      End
      Begin VB.Label Label13 
         Caption         =   "Solución:"
         Height          =   240
         Left            =   7275
         TabIndex        =   24
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
      Begin VB.Label Label11 
         Caption         =   "Fases:"
         Height          =   240
         Left            =   4800
         TabIndex        =   23
         Top             =   375
         Width           =   765
      End
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
      Height          =   420
      Left            =   150
      TabIndex        =   1
      Top             =   3750
      Width           =   1440
   End
   Begin VB.CommandButton Command1 
      Caption         =   "&Cerrar"
      BeginProperty Font 
         Name            =   "Arial"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   420
      Left            =   7425
      TabIndex        =   0
      Top             =   3750
      Width           =   1215
   End
End
Attribute VB_Name = "Iaspei"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

Private Sub Command1_Click()
    Unload Iaspei
End Sub

Private Sub Command10_Click()
' nuevo
Dim Bandera As Integer
Dim d(100, 100), info(100), Aux, aux1, fases, nombre As String
Dim Cont, j, m As Integer
Dim X As Boolean
Dim c1, c2, b1, Sum, Prom As Variant
Dim lat, lon, prof, corrseg As String
' nuevo
Dim indicador As Long
Dim inicio, final, espera As Single
Dim www As Long
Dim FechaAntes, FechaDespues, Fecha As Variant
Dim i, indice, ind, indice2, ind2, num As Integer
Dim IndiceConv As Integer
Dim IndicadorFecha As Boolean
Dim archivo, NombArch, NombArch2 As String


File4.Refresh
File5.Refresh
File6.Refresh
File7.Refresh

If Label4.Caption = "" And (Check1.Value = 1 Or Check2.Value = 1) Then
    MsgBox "Debe escoger un archivo de fases", 48, "Alerta"
    Exit Sub
ElseIf Check1.Value = 0 And Check2.Value = 0 Then
    Exit Sub
End If


If Check1.Value = 1 Then
    If Not (Left(Label4.Caption, 5) = "Phase" Or _
        Left(Label4.Caption, 5) = "phase" Or _
        Left(Label4.Caption, 5) = "PHASE" Or _
        Label4.Caption = "fase.pha" Or _
        Label4.Caption = "FASE.PHA") Then
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



archivo = ""

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


 Open "C:\IASPEI\FastHypo\convert.in" For Output As #4
 
 
 
 Print #4, Label4.Caption
 Print #4, "2"

 Close #4

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
 File4.Refresh
 File5.Refresh
 File6.Refresh
 File7.Refresh

 File5.SetFocus

 ind = 0

 NombArch = Label4.Caption
 'fases = NombArch
 i = 1
 Do While i <= File4.ListCount
        If File4.List(i - 1) = NombArch Then
            indice = i - 1
            ind = 1
        End If
    i = i + 1
 Loop

 If File5.ListCount > 0 Then
  
  FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(0))
  archivo = File5.List(0)
  
  i = 1
  IndiceConv = 0
  num = File5.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i)) >= _
        FechaDespues Then

        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i))
        archivo = File5.List(i)
        IndiceConv = i
    End If
  i = i + 1
  
  Loop
  
  File5.Selected(IndiceConv) = True
  
  If IndicadorFecha = False Then
    If FechaDespues = FechaAntes Then
        
        File5.ListIndex = -1
        File6.ListIndex = -1
        File7.ListIndex = -1
        
        If ind = 1 Then
            File4.Selected(indice) = True
        End If
        
        MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & NombArch, 48, "Alerta"
        
        
        Exit Sub
    End If
  End If
  
  
 Else
    
    File5.ListIndex = -1
    File6.ListIndex = -1
    File7.ListIndex = -1
    If ind = 1 Then
        File4.Selected(indice) = True
    End If
    
    MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & NombArch, 48, "Alerta"
    
    
    Exit Sub
 End If


End If



'-------------------------------
If Check2.Value = 1 Then
    If archivo = "" Then
        archivo = Label4.Caption
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


 Open "C:\IASPEI\FastHypo\fpong.in" For Output As #4

 Print #4, Text1.Text
 Print #4, "y"
 Print #4, "r"
 Print #4, archivo
 Print #4, "n"
 Print #4, Format(Text5.Text, "0")
 Print #4, Format(Text2.Text, "0.000") & "," & Format(Text3.Text, "0.000") _
           & "," & Format(Text4.Text, "0.000") & ",0"
 Print #4, "n"
 Print #4, "done"
 Close #4

 activa = GetActiveWindow()
 indicador = Shell("C:\Iaspei\FastHypo\Fpongbat.bat", 3)
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

 ind2 = 0
 NombArch2 = Left(archivo, Len(archivo) - 1)
 i = 1
 Do While i <= File5.ListCount
        If File5.List(i - 1) = (NombArch2 & "P") Then
            indice2 = i - 1
            ind2 = 1
        End If
    i = i + 1
 Loop


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
        "Revise los datos que introdujo o el contenido del archivo " & archivo, 48, "Alerta"
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        If ind = 1 Then
            File4.Selected(indice) = True
        End If
        
        File6.ListIndex = -1
        File7.ListIndex = -1
        Exit Sub
    Else
        
        On Error GoTo ErrorArchivo
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(archivo, Len(archivo) - 1) & "L"
        File6.Refresh
        
        ind2 = 0
        i = 1
        Do While i <= File6.ListCount
            If File6.List(i - 1) = (NombArch2 & "L") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File6.Selected(indice2) = True
        End If
        
        
        
        ind2 = 0
        i = 1
        Do While i <= File7.ListCount
            If File7.List(i - 1) = (NombArch2 & "S") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File7.Selected(indice2) = True
        End If
        
        
    End If
  Else
    
        On Error GoTo ErrorArchivo
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(archivo, Len(archivo) - 1) & "L"
        File6.Refresh
        
        ind2 = 0
        i = 1
        Do While i <= File6.ListCount
            If File6.List(i - 1) = (NombArch2 & "L") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File6.Selected(indice2) = True
        End If
        
        
        
        ind2 = 0
        i = 1
        Do While i <= File7.ListCount
            If File7.List(i - 1) = (NombArch2 & "S") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File7.Selected(indice2) = True
        End If
    
    
    
    
  End If
  
  
Else
        MsgBox "El programa FPONG no se ejecutó adecuadamente" & Chr(13) & _
        "Revise los datos que introdujo o el contenido del archivo " & archivo, 48, "Alerta"
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        If ind = 1 Then
            File4.Selected(indice) = True
        End If
        
        File6.ListIndex = -1
        File7.ListIndex = -1
        Exit Sub
End If


End If



If Check1.Value = 1 And Check2.Value = 1 Then
   On Error GoTo ErrorPhase
    NombArch2 = Right(NombArch2, 7)
    NombArch2 = Left(NombArch2, 4) & Right(NombArch2, 2)
    NombArch2 = "Phase" & Left(NombArch2, 3) & "." & Right(NombArch2, 3)
    
    Name "C:\Iaspei\FastHypo\" & NombArch As _
         "C:\Iaspei\FastHypo\" & NombArch2
    File4.Refresh
    
    ind = 1
    i = 1
    Do While i <= File4.ListCount
        If File4.List(i - 1) = NombArch2 Then
            indice = i - 1
        End If
      i = i + 1
    Loop
    
End If


If ind = 1 Then
        File4.Selected(indice) = True
End If
' en la variable nombre se encuentra el archivo *.l
' en la variable fases se encuentra el archivo phase*.*
' el archivo mag2000.txt se encuentra las variables
' b,c1,c2 para el calculo de magnitudes
' En el archivo mag2000.txt en las cuatro primeras posiciones
' se encuentran el nombre de las estaciones, estas deben estar
' completamente igual que el nombre de las estaciones que se
' encuentran en los archivos *.l y phase*.*


'Print fases
nombre = archivo
nombre = Left(nombre, Len(nombre) - 1) & "L"
fases = "Phase" & Mid(nombre, 3, 3) & "." & Mid(nombre, 6, 1) & Mid(nombre, 8, 2)
'-----------------------------------------------------
'-----------------------------------------------------
'-----------------------------------------------------
'Cálculo de la Magnitud

Cont = 0
Bandera = 0
Open "C:\IASPEI\FastHypo\" & nombre For Input As #10
Do While Not EOF(10)
Line Input #10, a$
c$ = Input(2, #10)
X = c$ Like " [A-Z]"
If X = True Then
            Cont = Cont + 1
End If
b$ = Input(6, #10)
If b$ = "sta   " Then
             
                 Bandera = 1
                 d(1, 1) = b$
                 d(2, 1) = Input(5, #10)
                 Line Input #10, a$
End If
If Bandera = 1 Then
    For i = 2 To Cont + 1
       c$ = Input(2, #10)
       d(1, i) = Input(6, #10)
       d(2, i) = Input(5, #10)
       Line Input #10, a$
    Next
    Exit Do
End If
Loop

Do While Not EOF(10)
Line Input #10, a$
aux1 = Mid(a$, 1, 6)
If aux1 = " event" Then
                   For i = 1 To 7
                    info(i) = a$
                    Line Input #10, a$
                   Next
                   Exit Do
End If
Loop
Close 10

Open "c:\Iaspei\FastHypo\" & fases For Input As #20
d(3, 1) = "Coda"
For i = 1 To Cont + 1
Line Input #20, a$
b$ = Right(a$, 7)
d(3, i + 1) = b$
Next
Close 20
For i = 1 To Cont + 1
  d(1, 1) = Trim(d(1, 1))
  d(2, 1) = Trim(d(2, 1))
  d(3, 1) = Trim(d(3, 1))
  d(1, i + 1) = Trim(d(1, i + 1))
  If d(1, i + 1) = "UNI" Then
                          d(1, i + 1) = "UNI "
  End If
  d(2, i + 1) = Val(d(2, i + 1))
  d(3, i + 1) = Val(d(3, i + 1))
Next

Open "c:\Iaspei\Mag2000.txt" For Input As #30
j = 1
i = 1
d(4, 1) = "Mag"
Do While j < Cont + 1
Line Input #30, a$
Aux = Mid(a$, 1, 4)
If d(1, i + 1) = Aux Then
           j = j + 1
           b$ = Mid(a$, 5, 8)
           b1 = Val(b$)
           b$ = Mid(a$, 14, 8)
           c1 = Val(b$)
           c$ = Mid(a$, 23, 8)
           c2 = Val(c$)
           If (b1 = 0) And (c1 = 0) And (c2 = 0) Then
            d(4, i + 1) = "NMG"
            i = i + 1
            Seek 30, 1
            Else
             If d(3, i + 1) <> 0 Then
                                  d(4, i + 1) = b1 + c1 * Log10(d(3, i + 1)) + c2 * d(2, i + 1)
                                  d(4, i + 1) = Val(d(4, i + 1))
                                  i = i + 1
                                  Seek 30, 1
            
             Else
             d(3, i + 1) = 0
             d(4, i + 1) = "NMG"
             i = i + 1
             Seek 30, 1
             End If
            End If
            
End If
Loop
Close 30
Sum = 0
m = 0
For i = 1 To Cont
If d(4, i + 1) <> "NMG" Then
                   m = m + 1
                   Sum = Sum + d(4, i + 1)
                       
End If
Next
If m = 0 And Sum = 0 Then
                     Prom = "No Existe Magnitud"
                     Else
                     Prom = Sum / m
End If
Fecha = Mid(info(1), 17, 15)
lat = Mid(info(4), 2, 10)
lon = Mid(info(5), 2, 10)
prof = Mid(info(6), 2, 10)
corrseg = Mid(info(7), 2, 10)
'''''Fecha = Trim(Fecha)'
lat = Trim(lat)
lon = Trim(lon)
prof = Trim(prof)
corrseg = Trim(corrseg)

Form3.Enabled = True
Form3.Show
Form3.Print
Form3.Print
Form3.Print "     * Fecha y Hora del Sismo: " + Fecha;
Form3.Print "  " + corrseg
Form3.Print
Form3.Print "     * Latitud: " + lat
Form3.Print
Form3.Print "     * Longitud: " + lon
Form3.Print
Form3.Print "     * Profundidad (km): " + prof

''Me.Print d(1, 1), d(2, 1), d(3, 1), d(4, 1)
''For i = 2 To Cont + 1
''        Me.Print d(1, i), Format(d(2, i), "000.00"), Format(d(3, i), "00.00"), Format(d(4, i), "0.0")
''Next
''Me.Print
''Me.Font.Bold = True
''Me.Print "Promedio de las Magnitudes............"; Format(Prom, "#.#")

Form3.Print
Form3.FontBold = True
Form3.Print "    * Magnitud (Md): "; Format(Prom, "#.#")
Form3.FontBold = False
Form3.CurrentX = 1
Form3.CurrentY = 1
'Open "c:\Iaspei\FastHypo\" & nombre For Append As #10
'Print #10, "CALCULO DE LA MAGNITUD"
'Print #10,
'Print #10, d(1, 1), d(2, 1), d(3, 1), d(4, 1)
'For i = 2 To Cont + 1
'Print #10, d(1, i), Format(d(2, i), "000.00"), Format(d(3, i), "00.00"), Format(d(4, i), "0.0")
'Next
'Print #10,
'Print #10, "Promedio de las Magnitudes: "; Format(Prom, "#.#")
'Close (10)
Open "c:\Iaspei\FastHypo\Auxiliar.txt" For Output As #100
Print #100, "CALCULO DE LA MAGNITUD"
Print #100,
Print #100, d(1, 1), d(2, 1), d(3, 1), d(4, 1)
For i = 2 To Cont + 1
Print #100, d(1, i), Format(d(2, i), "000.00"), Format(d(3, i), "00.00"), Format(d(4, i), "0.0")
Next
Print #100,
Print #100, "Promedio de las Magnitudes: "; Format(Prom, "#.#")
Close (100)
Open "c:\Iaspei\FastHypo\" & nombre For Input As #200
Open "c:\Iaspei\FastHypo\" & Mid(nombre, 1, 6) & Mid(nombre, 8, 2) & "." & "rsa" For Output As #300
Do While Not EOF(200)
Line Input #200, a$
Print #300, a$
Loop
Open "c:\Iaspei\FastHypo\Auxiliar.txt" For Input As #400
Do While Not EOF(400)
Line Input #400, a$
Print #300, a$
Loop
Close (400)
Close (300)
Close (200)

'''hasta aqui se el cálculo de la magnitud
'----------------------------------------------------------------
'----------------------------------------------------------------
'----------------------------------------------------------------


MsgBox "Proceso Terminado 2", vbDefaultButton1, "CONVERT/FPONG"


Exit Sub

ErrorArchivo:
    Kill ("C:\Iaspei\FastHypo\" & Left(archivo, Len(archivo) - 1) & "L")
    Resume
    Exit Sub
    
ErrorPhase:
    Kill ("C:\Iaspei\FastHypo\" & NombArch2)
    Resume

End Sub

Private Sub Command11_Click()
Dim indicador As Long
Dim archivo As String

If File5.ListCount > 0 And File5.ListIndex >= 0 Then
    archivo = File5.Path & "\" & File5.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & archivo, 3)
End If
End Sub


Private Sub Command12_Click()
Dim indicador As Long
Dim archivo As String

If File6.ListCount > 0 And File6.ListIndex >= 0 Then
    archivo = File6.Path & "\" & File6.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & archivo, 3)
End If
End Sub


Private Sub Command13_Click()
Dim indicador As Long
Dim archivo As String

If File7.ListCount > 0 And File7.ListIndex >= 0 Then
    archivo = File7.Path & "\" & File7.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & archivo, 3)
End If

End Sub

Private Sub Command14_Click()
File4.Refresh
File5.Refresh
File6.Refresh
File7.Refresh

End Sub

Private Sub Command15_Click()
Dim archivo, Nuevo As String
Dim indice, i As Integer
If File4.ListCount > 0 And File4.ListIndex >= 0 Then
    
    archivo = File4.filename
    Nuevo = InputBox("Introduzca el nuevo nombre", "Renombrar Archivo de Fases", archivo)
        
    On Error GoTo ErrorNombre
    Name (File4.Path & "\" & archivo) As (File4.Path & "\" & Nuevo)
    File4.Refresh
    
    i = 1
    Do While i <= File4.ListCount
        If File4.List(i - 1) = Nuevo Then
            indice = i - 1
        End If
        i = i + 1
    Loop
    
    File4.Selected(indice) = True
    
End If

Exit Sub

ErrorNombre:
    Exit Sub

End Sub

Private Sub Command16_Click()
Dim archivo As String
Dim indicador As Integer

If File5.ListCount > 0 And File5.ListIndex >= 0 Then
    archivo = Left(File5.filename, Len(File5.filename) - 1)
    
    indicador = MsgBox("¿Está seguro de que desea borarr los siguientes archivos?" & _
                    Chr(13) & Space(4) & archivo & "P" & Chr(13) & Space(4) & archivo & "L" _
                    & Chr(13) & Space(4) & archivo & "S", vbYesNo, "Alerta")
    

    If indicador = 6 Then
    
        On Error GoTo ErrorBorrar
        
        Kill (File5.Path & "\" & archivo & "P")
        Kill (File5.Path & "\" & archivo & "L")
        Kill (File5.Path & "\" & archivo & "S")
        
        File5.Refresh
        File6.Refresh
        File7.Refresh
        Label4.Caption = ""
    
    
    End If
End If

Exit Sub

ErrorBorrar:
Resume Next

End Sub

Private Sub Command2_Click()
Dim archivo As String
Dim RutaXplay As String
Dim indicador As Double

If File1.ListCount <> 0 Then
    archivo = File1.Path & "\" & File1.filename
    RutaXplay = "C:\Iaspei\Pcsuds\Xplayv.exe"
    indicador = Shell(RutaXplay & " " & archivo, 3)
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
Dim archivo, RutaDemux, RutaIrig As String
    indice = 1
    espera = 0.7
    RutaDemux = "C:\Iaspei\Pcsuds\Demux.exe"
    RutaIrig = "C:\Iaspei\Pcsuds\Irig.exe"
    
    If Option1.Value = True And File2.ListIndex <> -1 Then
    
      Do While indice <= 10000
        If indice <= File2.ListCount Then
            
            If File2.Selected(indice - 1) = True Then
                
                archivo = File1.Path & "\" & File2.List(indice - 1)
                activa = GetActiveWindow()
                
                'IRIG
                indicador = Shell(RutaIrig & " " & archivo, 3)
                
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
                
                indicador = Shell(RutaDemux & " " & archivo, 3)
                
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
      MsgBox "Proceso terminado 3 satisfactoriamente", vbOKOnly, "Demux/Irig"
    
    ElseIf Option2.Value = True Then
    RutaDemux = "C:\Iaspei\Pcsuds\Demux.exe"
    RutaIrig = "C:\Iaspei\Pcsuds\Irig.exe"

      Do While indice <= File2.ListCount
                    
        
                archivo = File1.Path & "\" & File2.List(indice - 1)
                                
                activa = GetActiveWindow()
                
                'IRIG
                indicador = Shell(RutaIrig & " " & archivo, 3)
                
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
                
                indicador = Shell(RutaDemux & " " & archivo, 3)
                
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
      MsgBox "Proceso terminado 4", vbOKOnly, "Demux/Irig"

    End If
    File2.Refresh
    File2.SetFocus
    
End Sub


Private Sub Command5_Click()
Dim archivo, NombArch As String
Dim RutaSuds As String
Dim indicador As Double
Dim indice, i, NumDespues As Integer


If File3.ListCount <> 0 And File3.ListIndex >= 0 Then
    NombArch = File3.filename
    archivo = File3.Path & "\" & File3.filename
    indice = File3.ListIndex
    RutaSuds = "C:\Iaspei\Pcsuds\Sudspick.exe"
    indicador = Shell(RutaSuds & " " & archivo, 3)
    
    File2.Refresh
    File3.Refresh
    NumDespues = File3.ListCount
    
    i = 1
    Do While i <= NumDespues
        If File3.List(i - 1) = NombArch Then
            indice = i - 1
            indicador = 1
        End If
        i = i + 1
    Loop
    
End If
File2.Refresh
File3.Refresh

If indicador = 1 Then
    File3.Selected(indice) = True
End If

End Sub


Private Sub Command6_Click()
Dim archivo, ArchSal, NombArch As String
Dim RutaXtrhy As String
Dim indicador As Double
Dim Salida As String
Dim activa As Long
Dim espera As Single
Dim IndicadorFecha As Boolean
Dim i, indice, num, NumDespues As Integer
Dim www As Integer

espera = 0.7
IndicadorFecha = False

If File3.ListCount <> 0 And File3.ListIndex >= 0 Then
    
    File4.Refresh
    NombArch = File3.filename
    
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
        
    '---------
    Salida = "fase.pha"
    
    ArchSal = Salida
    Salida = "C:\Iaspei\FastHypo" & "\" & Salida
    
    archivo = File3.Path & "\" & File3.filename
    Arch = File3.filename
    
    RutaXtrhy = "C:\Iaspei\Pcsuds\Xtrhy71.exe"
    
    activa = GetActiveWindow()
                
    indicador = Shell(RutaXtrhy & " " & archivo & " " & Salida, 3)
                
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
    
    NumDespues = File3.ListCount
    
    i = 1
    Do While i <= NumDespues
        If File3.List(i - 1) = NombArch Then
            indice = i - 1
            indicador = 1
        End If
        i = i + 1
    Loop
    
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
                If indicador = 1 Then
                    File3.Selected(indice) = True
                End If
                
                
                Exit Sub
            End If
        End If
    Else
        File5.ListIndex = -1
        File6.ListIndex = -1
        File7.ListIndex = -1
        MsgBox "No fue posible crear el archivo '" & ArchSal _
                & "' que contiene las fases", 48, "Alerta"
        If indicador = 1 Then
                    File3.Selected(indice) = True
        End If
        Exit Sub
    End If

    If indicador = 1 Then
        File3.Selected(indice) = True
    End If
    
    Label4.Caption = "fase.pha"
    Check1.Value = 1
    Check2.Value = 1
    File5.ListIndex = -1
    File6.ListIndex = -1
    File7.ListIndex = -1
    MsgBox "Proceso terminado 5", vbDefaultButton1, "FASES"
    Label4.Caption = "fase.pha"
    
End If


End Sub

Private Sub Command7_Click()
Dim indicador As Long
Dim archivo As String

If File4.ListCount > 0 And File4.ListIndex >= 0 Then
    Label4.Caption = File4.filename
    archivo = File4.Path & "\" & File4.filename
    indicador = Shell("C:\Iaspei\Editor\Wordpad.exe " & archivo, 3)
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
Static Function Log10(X)
    Log10 = Log(X) / Log(10#)
End Function
Private Sub Command9_Click()
' nuevo
Dim Bandera As Integer
Dim d(100, 100), info(100), Aux, aux1, fases, nombre As String
Dim Cont, j, m As Integer
Dim X As Boolean
Dim c1, c2, b1, Sum, Prom As Variant
Dim lat, lon, prof, corrseg As String
' nuevo
Dim indicador As Long
Dim inicio, final, espera As Single
Dim www As Long
Dim FechaAntes, FechaDespues, Fecha As Variant
Dim i, indice, ind, indice2, ind2, num As Integer
Dim IndiceConv As Integer
Dim IndicadorFecha As Boolean
Dim archivo, NombArch, NombArch2 As String
File4.Refresh
File5.Refresh
File6.Refresh
File7.Refresh

If Label4.Caption = "" And (Check1.Value = 1 Or Check2.Value = 1) Then
    MsgBox "Debe escoger un archivo de fases", 48, "Alerta"
    Exit Sub
ElseIf Check1.Value = 0 And Check2.Value = 0 Then
    Exit Sub
End If


If Check1.Value = 1 Then
    If Not (Left(Label4.Caption, 5) = "Phase" Or _
        Left(Label4.Caption, 5) = "phase" Or _
        Left(Label4.Caption, 5) = "PHASE" Or _
        Label4.Caption = "fase.pha" Or _
        Label4.Caption = "FASE.PHA") Then
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



archivo = ""

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


 Open "C:\IASPEI\FastHypo\convert.in" For Output As #4
 
 
 
 Print #4, Label4.Caption
 Print #4, "2"

 Close #4

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
 File4.Refresh
 File5.Refresh
 File6.Refresh
 File7.Refresh

 File5.SetFocus

 ind = 0
 NombArch = Label4.Caption
 'fases = NombArch
 i = 1
 Do While i <= File4.ListCount
        If File4.List(i - 1) = NombArch Then
            indice = i - 1
            ind = 1
        End If
    i = i + 1
 Loop

 If File5.ListCount > 0 Then
  
  FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(0))
  archivo = File5.List(0)
  
  i = 1
  IndiceConv = 0
  num = File5.ListCount
  Do While i < num
    If FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i)) >= _
        FechaDespues Then

        FechaDespues = FileDateTime("C:\Iaspei\FastHypo\" & File5.List(i))
        archivo = File5.List(i)
        IndiceConv = i
    End If
  i = i + 1
  
  Loop
  
  File5.Selected(IndiceConv) = True
  
  If IndicadorFecha = False Then
    If FechaDespues = FechaAntes Then
        
        File5.ListIndex = -1
        File6.ListIndex = -1
        File7.ListIndex = -1
        
        If ind = 1 Then
            File4.Selected(indice) = True
        End If
        
        MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & NombArch, 48, "Alerta"
        
        
        Exit Sub
    End If
  End If
  
  
 Else
    
    File5.ListIndex = -1
    File6.ListIndex = -1
    File7.ListIndex = -1
    If ind = 1 Then
        File4.Selected(indice) = True
    End If
    
    MsgBox "No fue posible crear el archivo de fases" & Chr(13) & _
        "Revise el contenido del archivo " & NombArch, 48, "Alerta"
    
    
    Exit Sub
 End If


End If



'-------------------------------
If Check2.Value = 1 Then
    If archivo = "" Then
        archivo = Label4.Caption
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


 Open "C:\IASPEI\FastHypo\fast.in" For Output As #4

 Print #4, Text1.Text
 Print #4, "y"
 Print #4, "r"
 Print #4, archivo
 Print #4, "n"
 Print #4, Format(Text5.Text, "0")
 Print #4, Format(Text2.Text, "0.000") & "," & Format(Text3.Text, "0.000") _
           & "," & Format(Text4.Text, "0.000") & ",0"
 Print #4, "n"
 Print #4, "done"
 Close #4

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

 ind2 = 0
 NombArch2 = Left(archivo, Len(archivo) - 1)
 i = 1
 Do While i <= File5.ListCount
        If File5.List(i - 1) = (NombArch2 & "P") Then
            indice2 = i - 1
            ind2 = 1
        End If
    i = i + 1
 Loop


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
        "Revise los datos que introdujo o el contenido del archivo " & archivo, 48, "Alerta"
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        If ind = 1 Then
            File4.Selected(indice) = True
        End If
        
        File6.ListIndex = -1
        File7.ListIndex = -1
        Exit Sub
    Else
        
        On Error GoTo ErrorArchivo
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(archivo, Len(archivo) - 1) & "L"
        File6.Refresh
        
        ind2 = 0
        i = 1
        Do While i <= File6.ListCount
            If File6.List(i - 1) = (NombArch2 & "L") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File6.Selected(indice2) = True
        End If
        
        
        
        ind2 = 0
        i = 1
        Do While i <= File7.ListCount
            If File7.List(i - 1) = (NombArch2 & "S") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File7.Selected(indice2) = True
        End If
        
        
    End If
  Else
    
        On Error GoTo ErrorArchivo
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        Name "C:\Iaspei\FastHypo\Lp.lst" As _
            "C:\Iaspei\FastHypo\" & Left(archivo, Len(archivo) - 1) & "L"
        File6.Refresh
        
        ind2 = 0
        i = 1
        Do While i <= File6.ListCount
            If File6.List(i - 1) = (NombArch2 & "L") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File6.Selected(indice2) = True
        End If
        
        
        
        ind2 = 0
        i = 1
        Do While i <= File7.ListCount
            If File7.List(i - 1) = (NombArch2 & "S") Then
                indice2 = i - 1
                ind2 = 1
            End If
            i = i + 1
        Loop
        
        If ind2 = 1 Then
            File7.Selected(indice2) = True
        End If
    
    
    
    
  End If
  
  
Else
        MsgBox "El programa FAST no se ejecutó adecuadamente" & Chr(13) & _
        "Revise los datos que introdujo o el contenido del archivo " & archivo, 48, "Alerta"
        If ind2 = 1 Then
            File5.Selected(indice2) = True
        End If
        
        If ind = 1 Then
            File4.Selected(indice) = True
        End If
        
        File6.ListIndex = -1
        File7.ListIndex = -1
        Exit Sub
End If


End If



If Check1.Value = 1 And Check2.Value = 1 Then
   On Error GoTo ErrorPhase
    NombArch2 = Right(NombArch2, 7)
    NombArch2 = Left(NombArch2, 4) & Right(NombArch2, 2)
    NombArch2 = "Phase" & Left(NombArch2, 3) & "." & Right(NombArch2, 3)
    
    Name "C:\Iaspei\FastHypo\" & NombArch As _
         "C:\Iaspei\FastHypo\" & NombArch2
    File4.Refresh
    
    ind = 1
    i = 1
    Do While i <= File4.ListCount
        If File4.List(i - 1) = NombArch2 Then
            indice = i - 1
        End If
      i = i + 1
    Loop
    
End If


If ind = 1 Then
        File4.Selected(indice) = True
End If

' en la variable nombre se encuentra el archivo *.l
' en la variable fases se encuentra el archivo phase*.*
' el archivo mag2000.txt se encuentra las variables
' b,c1,c2 para el calculo de magnitudes
' En el archivo mag2000.txt en las cuatro primeras posiciones
' se encuentran el nombre de las estaciones, estas deben estar
' completamente igual que el nombre de las estaciones que se
' encuentran en los archivos *.l y phase*.*



nombre = archivo
nombre = Left(nombre, Len(nombre) - 1) & "L"
fases = "Phase" & Mid(nombre, 3, 3) & "." & Mid(nombre, 6, 1) & Mid(nombre, 8, 2)
'-----------------------------------------------------
'-----------------------------------------------------
'-----------------------------------------------------
'Cálculo de la Magnitud

Cont = 0
Bandera = 0
Open "C:\IASPEI\FastHypo\" & nombre For Input As #10
Do While Not EOF(10)
Line Input #10, a$
c$ = Input(2, #10)
X = c$ Like " [A-Z]"
If X = True Then
            Cont = Cont + 1
End If
b$ = Input(6, #10)
If b$ = "sta   " Then
             
                 Bandera = 1
                 d(1, 1) = b$
                 d(2, 1) = Input(5, #10)
                 Line Input #10, a$
End If
If Bandera = 1 Then
    For i = 2 To Cont + 1
       c$ = Input(2, #10)
       d(1, i) = Input(6, #10)
       d(2, i) = Input(5, #10)
       Line Input #10, a$
    Next
    Exit Do
End If
Loop

Do While Not EOF(10)
Line Input #10, a$
aux1 = Mid(a$, 1, 6)
If aux1 = " event" Then
                   For i = 1 To 7
                    info(i) = a$
                    Line Input #10, a$
                   Next
                   Exit Do
End If
Loop
Close 10

Open "c:\Iaspei\FastHypo\" & fases For Input As #20
d(3, 1) = "Coda"
For i = 1 To Cont + 1
Line Input #20, a$
b$ = Right(a$, 7)
d(3, i + 1) = b$
Next
Close 20
For i = 1 To Cont + 1
  d(1, 1) = Trim(d(1, 1))
  d(2, 1) = Trim(d(2, 1))
  d(3, 1) = Trim(d(3, 1))
  d(1, i + 1) = Trim(d(1, i + 1))
  If d(1, i + 1) = "UNI" Then
                          d(1, i + 1) = "UNI "
  End If
  d(2, i + 1) = Val(d(2, i + 1))
  d(3, i + 1) = Val(d(3, i + 1))
Next
Open "c:\Iaspei\Mag2000.txt" For Input As #30
j = 1
i = 1
d(4, 1) = "Mag"
Do While j < Cont + 1
Line Input #30, a$
Aux = Mid(a$, 1, 4)
If d(1, i + 1) = Aux Then
           j = j + 1
           b$ = Mid(a$, 5, 8)
           b1 = Val(b$)
           b$ = Mid(a$, 14, 8)
           c1 = Val(b$)
           c$ = Mid(a$, 23, 8)
           c2 = Val(c$)
           If (b1 = 0) And (c1 = 0) And (c2 = 0) Then
            d(4, i + 1) = "NMG"
            i = i + 1
            Seek 30, 1
            Else
            If d(3, i + 1) <> 0 Then
                                  d(4, i + 1) = b1 + c1 * Log10(d(3, i + 1)) + c2 * d(2, i + 1)
                                  d(4, i + 1) = Val(d(4, i + 1))
                                  i = i + 1
                                  Seek 30, 1
            
            Else
            d(3, i + 1) = 0
            d(4, i + 1) = "NMG"
            i = i + 1
            Seek 30, 1
            End If
           End If
End If
Loop
Close 30
Sum = 0
m = 0
For i = 1 To Cont
If d(4, i + 1) <> "NMG" Then
                   'If d(3, i + 1) <> 0 Then
                   m = m + 1
                   Sum = Sum + d(4, i + 1)
                   'End If
End If
Next
If m = 0 And Sum = 0 Then
                     Prom = "No Existe Magnitud"
                     Else
                     Prom = Sum / m
End If
Fecha = Mid(info(1), 17, 15)
lat = Mid(info(4), 2, 10)
lon = Mid(info(5), 2, 10)
prof = Mid(info(6), 2, 10)
corrseg = Mid(info(7), 2, 10)
lat = Trim(lat)
lon = Trim(lon)
prof = Trim(prof)
corrseg = Trim(corrseg)

Form3.Enabled = True
Form3.Show
Form3.Print
Form3.Print
Form3.Print "     * Fecha y Hora del Sismo: " + Fecha;
Form3.Print "  " + corrseg
Form3.Print
Form3.Print "     * Latitud: " + lat
Form3.Print
Form3.Print "     * Longitud: " + lon
Form3.Print
Form3.Print "     * Profundidad (km): " + prof

''Me.Print d(1, 1), d(2, 1), d(3, 1), d(4, 1)
''For i = 2 To Cont + 1
''        Me.Print d(1, i), Format(d(2, i), "000.00"), Format(d(3, i), "00.00"), Format(d(4, i), "0.0")
''Next
''Me.Print
''Me.Font.Bold = True
''Me.Print "Promedio de las Magnitudes............"; Format(Prom, "#.#")

Form3.Print
Form3.FontBold = True
Form3.Print "    * Magnitud (Md): "; Format(Prom, "#.#")
Form3.FontBold = False
Form3.CurrentX = 1
Form3.CurrentY = 1
'Open "c:\Iaspei\FastHypo\" & nombre For Append As #10
'Print #10, "CALCULO DE LA MAGNITUD"
'Print #10,
'Print #10, d(1, 1), d(2, 1), d(3, 1), d(4, 1)
'For i = 2 To Cont + 1
'Print #10, d(1, i), Format(d(2, i), "000.00"), Format(d(3, i), "00.00"), Format(d(4, i), "0.0")
'Next
'Print #10,
'Print #10, "Promedio de las Magnitudes: "; Format(Prom, "#.#")
'Close (10)
Open "c:\Iaspei\FastHypo\Auxiliar.txt" For Output As #100
Print #100, "CALCULO DE LA MAGNITUD"
Print #100,
Print #100, d(1, 1), d(2, 1), d(3, 1), d(4, 1)
For i = 2 To Cont + 1
Print #100, d(1, i), Format(d(2, i), "000.00"), Format(d(3, i), "00.00"), Format(d(4, i), "0.0")
Next
Print #100,
Print #100, "Promedio de las Magnitudes: "; Format(Prom, "#.#")
Close (100)
Open "c:\Iaspei\FastHypo\" & nombre For Input As #200
Open "c:\Iaspei\FastHypo\" & Mid(nombre, 1, 6) & Mid(nombre, 8, 2) & "." & "rsa" For Output As #300
Do While Not EOF(200)
Line Input #200, a$
Print #300, a$
Loop
Open "c:\Iaspei\FastHypo\Auxiliar.txt" For Input As #400
Do While Not EOF(400)
Line Input #400, a$
Print #300, a$
Loop
Close (400)
Close (300)
Close (200)

'''hasta aqui se el cálculo de la magnitud
'----------------------------------------------------------------
'----------------------------------------------------------------
'----------------------------------------------------------------




MsgBox "Proceso Terminado 1", vbDefaultButton1, "CONVERT/FAST"


Exit Sub

ErrorArchivo:
    Kill ("C:\Iaspei\FastHypo\" & Left(archivo, Len(archivo) - 1) & "L")
    Resume
    Exit Sub
    
ErrorPhase:
    Kill ("C:\Iaspei\FastHypo\" & NombArch2)
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
Dim archivo As String
Dim RutaXplay As String
Dim indicador As Double

    archivo = File1.Path & "\" & File1.filename
    RutaXplay = "C:\Iaspei\Pcsuds\Xplayv.exe"
    indicador = Shell(RutaXplay & " " & archivo, 3)

End Sub

Private Sub File1_KeyDown(KeyCode As Integer, Shift As Integer)
Dim archivo As String
Dim RutaXplay As String
Dim indicador As Double

If KeyCode = 13 Then

    If File1.ListCount <> 0 Then
        archivo = File1.Path & "\" & File1.filename
        RutaXplay = "C:\Iaspei\Pcsuds\Xplayv.exe"
        indicador = Shell(RutaXplay & " " & archivo, 3)
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
Label4.Caption = "fase.pha"
File4.Path = "C:\Iaspei\FastHypo"
File5.Path = "C:\Iaspei\FastHypo"
File6.Path = "C:\Iaspei\FastHypo"
File7.Path = "C:\Iaspei\FastHypo"
End Sub

Private Sub SSTab1_DblClick()

End Sub
