// app.js

const { useState,useEffect } = React;
//todo meter esto en una variable de entorno (Nombre del servicio, y el puerto)
const API_URL = 'http://localhost:5005';

function App() {
  const [motor, setMotor] = useState('PostgreSQL');
  const [terminoBusqueda, setTerminoBusqueda] = useState('');
  const [resultados, setResultados] = useState([]);
  const [cancionSeleccionada, setCancionSeleccionada] = useState(null);
  const [filtroLenguaje, setFiltroLenguaje] = useState('');
  const [filtroGenero, setFiltroGenero] = useState('');
  const [filtroPopularidad, setFiltroPopularidad] = useState(50);

  const manejarBusqueda = () => {
    // Simulación de búsqueda en base de datos
    setResultados([
      { 
        song_name: 'Canción 1',
        artist: 'Artista 1',
        genres: 'Pop; Rock',
        popularity: 80,
        language: 'es',
        lyric: 'primer verso\nsegundo verso', 
        score: 9.5,
        artist_link: '/link/artista1',
        song_link: '/link/cancion1.html'
      },
      { 
        song_name: 'Canción 2',
        artist: 'Artista 2',
        genres: 'Hip-Hop',
        popularity: 90,
        language: 'en',
        lyric: 'primer verso\nsegundo verso',
        score: 8.9,
        artist_link: '/link/artista2',
        song_link: '/link/cancion2.html'
      },
    ]);
  };

  const seleccionarCancion = (cancion) => {
    setCancionSeleccionada(cancion);
  };
  
  return (
    /*--------------------------------------------------------------------------------------*/
    /*--------------------esta es la parte principal, acá se muestra todo-------------------*/
    /*--------------------------------------------------------------------------------------*/
    <div className="contenedor-app">

    {/*-------------------------------------------------------------------------------------*/
    /*-------------este es el header, esta parte no cambia durante la ejecución-------------*/
    /*-------------contiene las cosas en dos contenedores separados por estética------------*/
    /*--------------------------------------------------------------------------------------*/}
      <header className="encabezado-app">

        {/*-------------------------------------------------------------------------------------*/
        /*-----------Título, un slogan inventado y lo principal, la barra de búsqueda-----------*/
        /*--------------------------------------------------------------------------------------*/}
        <div className="parte-principal">
          <h1>TuneStay</h1>
          <p>Tu hogar, al ritmo de tus canciones.</p>

          <div className="barra-busqueda">
            <input 
              type="text" 
              placeholder="Buscar por letra o artista..." 
              value={terminoBusqueda} 
              onChange={(e) => setTerminoBusqueda(e.target.value)} 
            />
            <button onClick={manejarBusqueda}>Buscar</button>
          </div>
        </div>
        
        {/*-------------------------------------------------------------------------------------*/
        /*-----------Todo lo relacionado a los filtros de búsqueda y cambiar el motor-----------*/
        /*--------------------------------------------------------------------------------------*/}
        <div className='parte-filtros'>

          {/*-------------------------------------------------------------------------------------*/
          /*------------------------------------Cambio de motor-----------------------------------*/
          /*--------------------------------------------------------------------------------------*/}
          <div className="controles-busqueda">
            <label>Motor de Búsqueda:</label>
            <select value={motor} onChange={(e) => setMotor(e.target.value)}>
              <option value="PostgreSQL">PostgreSQL</option>
              <option value="Mongo Atlas">Mongo Atlas</option>
            </select>
          </div>

          {/*-------------------------------------------------------------------------------------*/
          /*---------------------------------Filtros de búsqueda----------------------------------*/
          /*--------------------------------------------------------------------------------------*/}
          <div className="filtros">
            <label>Filtrar por Lenguaje:</label>
            <select value={filtroLenguaje} onChange={(e) => setFiltroLenguaje(e.target.value)}>
              <option value="">Todos</option>
              <option value="Español">Español</option>
              <option value="Inglés">Inglés</option>
              <option value="Francés">Francés</option>
            </select>

            <label>Filtrar por Género:</label>
            <select value={filtroGenero} onChange={(e) => setFiltroGenero(e.target.value)}>
              <option value="">Todos</option>
              <option value="Pop">Pop</option>
              <option value="Rock">Rock</option>
              <option value="Hip-Hop">Hip-Hop</option>
            </select>

            <label>Filtrar por Popularidad:</label>
            <input
              type="range"
              min="0"
              max="10"
              value={filtroPopularidad}
              onChange={(e) => setFiltroPopularidad(e.target.value)}
            />
            <span>{filtroPopularidad}</span>
          </div>
        </div>
        
      </header>

      <main className="seccion-resultados">
        {cancionSeleccionada ? (
          <DetallesCancion cancion={cancionSeleccionada} />
        ) : (
          <ResultadosBusqueda resultados={resultados} onSelect={seleccionarCancion} />
        )}
      </main>
    </div>
  );
}

function ResultadosBusqueda({ resultados, onSelect }) {
  return (
    <div className="lista-resultados">
      <h2>Resultados de Búsqueda</h2>
      {resultados.length > 0 ? (
        resultados.map((cancion, index) => (
          <div key={index} className="item-resultado" onClick={() => onSelect(cancion)}>
            <h3>{cancion.song_name} - {cancion.artist}</h3>
            <p>Género: {cancion.genres}, Popularidad: {cancion.popularity}, Lenguaje: {cancion.language}</p>
          </div>
        ))        
      ) : (
        <p>No se encontraron resultados</p>
      )}
    </div>
  );
}

function DetallesCancion({ cancion }) {
  const [apartamentos, setApartamentos] = useState([]);
  const [apartamentoSeleccionado, setApartamentoSeleccionado] = useState(null); // Estado para apartamento seleccionado

  const buscarApartamentos = () => {
    setApartamentos([
      { 
        name: 'Apartamento 1',
        description: 'Descripción A',
        reviews: ['fino lol', 'ta potente el apartamento'],
        summary: 'resumen 1',
      },
      { 
        name: 'Apartamento 2',
        description: 'Descripción B',
        reviews: ['gran lugar', 'cerca de todo'],
        summary: 'resumen 2',
      },
      { 
        name: 'Apartamento 3',
        description: 'Descripción C',
        reviews: ['guapo el dueño', 'me encantó la piscina'],
        summary: 'resumen 3',
      }
    ]);
  };

  return (
    <div className="detalles-cancion">
      <h2>{cancion.song_name} de {cancion.artist}</h2>
      <p><strong>Género:</strong> {cancion.genres}</p>
      <p><strong>Popularidad:</strong> {cancion.popularity}</p>
      <p><strong>Lenguaje:</strong> {cancion.language}</p>
      <p><strong>Score:</strong> {cancion.score}</p>

      {/*-------------------------------------------------------------------------------------*/
      /*---------------------------Div con scroll Y para la letra---------------------------- */
      /*--------------------------------------------------------------------------------------*/}
      <div style={{ display: 'flex', overflow:'auto'}}>
        <p><strong>Letra:</strong> {cancion.lyric.split('\n').map((linea, index) => (
          <span key={index}>{linea}<br /></span>
        ))}</p>
      </div>
      
      <div className='seccion-busqueda'>
        <textarea 
          rows={4} 
          className='buscar-letra' 
          placeholder='¡Copie y pegue aquí la sección de la letra en base a la que desea buscar!'
        ></textarea>
        <button onClick={buscarApartamentos}>Buscar apartamentos basados en la letra</button>
      </div>

      {apartamentos.length > 0 && (
        <div style={{ width: '80%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignContent: 'center' }}>
          <h3>Resultados de Apartamentos</h3>
          <div className="lista-resultados" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', width: '100%' }}>
            {apartamentos.map((apto, index) => (
              <div 
                key={index} 
                className="item-resultado" 
                onClick={() => setApartamentoSeleccionado(apto)} // Seleccionar apartamento al hacer clic
              >
                <h4>{apto.name}</h4>
                <p><strong>Resumen:</strong> {apto.summary}</p>
              </div>
            ))}
          </div>

          {/* Mostrar reseñas del apartamento seleccionado */}
          {apartamentoSeleccionado && (
            <div className="reseñas">
              <h4>Descripción completa de {apartamentoSeleccionado.name}:</h4>
              <ul>
                <li>{apartamentoSeleccionado.description}</li>
              </ul>
              <h4>Reseñas de {apartamentoSeleccionado.name}:</h4> {/* Cambiado a 'name' */}
              <ul>
                {apartamentoSeleccionado.reviews.map((resena, idx) => ( // Cambiado a 'reviews'
                  <li key={idx}>{resena}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <button onClick={() => window.location.reload()}>Volver a los resultados</button>
    </div>
  );
}

// Renderizar la aplicación
ReactDOM.render(<App />, document.getElementById('root'));